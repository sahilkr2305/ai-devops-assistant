import json


from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
)

from ai.llm import llm
from ai.prompts import (
    DEVOPS_SYSTEM_PROMPT,
    MEMORY_INSTRUCTION,
    RAG_INSTRUCTION,
)
from ai.memory import (
    get_project_memory,
    format_memory,
)
from ai.rag import retrieve_context

from database.database import (
    Base,
    engine,
    SessionLocal,
)
from database.models import (
    Project,
    ChatMessage,
)

from tools.registry import DEVOPS_TOOLS

from tools.safety import (
    is_dangerous_action,
    approval_message,
)

from tools.approval import (
    create_approval,
    get_approval,
    approve_action,
    reject_action,
    can_execute_approval,
    mark_executed,
)

from tools.audit import (
    create_audit_log,
    get_audit_logs,
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AI DevOps Assistant",
    version="11.1.2",
    description=(
        "AI-powered DevOps assistant with RAG, "
        "conversation memory, DevOps tools, "
        "multi-step reasoning, safety controls, "
        "approval workflow, project binding "
        "and audit logging."
    ),
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class ProjectCreate(BaseModel):
    name: str


class ChatRequest(BaseModel):
    project_id: int
    message: str


class ApprovalExecutionRequest(BaseModel):
    project_id: int


# ============================================================
# TOOL MAP
# ============================================================

TOOL_MAP = {
    tool.name: tool
    for tool in DEVOPS_TOOLS
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def extract_ai_text(content) -> str:
    """
    Extract plain text from an LLM response.
    """

    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)

            elif isinstance(item, dict):
                text = item.get("text")

                if text:
                    parts.append(str(text))

        return "\n".join(parts).strip()

    return str(content)


def serialize_tool_result(result):
    """
    Convert tool results into a string
    that can safely be passed back to the LLM.
    """

    if result is None:
        return ""

    if isinstance(result, str):
        return result

    try:
        return json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )

    except Exception:
        return str(result)


def get_tool_name(tool_call):
    """
    Support LangChain tool-call formats.
    """

    return (
        tool_call.get("name")
        or tool_call.get("function", {}).get("name")
    )


def get_tool_arguments(tool_call):
    """
    Extract tool arguments from a LangChain
    tool call.
    """

    arguments = (
        tool_call.get("args")
        or tool_call.get("function", {}).get("arguments")
        or {}
    )

    if isinstance(arguments, str):
        try:
            return json.loads(arguments)

        except json.JSONDecodeError:
            return {}

    return arguments


def execute_tool_call(
    tool_name: str,
    arguments: dict,
    approval_status: str | None = None,
):
    """
    Execute a registered DevOps tool.

    Dangerous tools require explicit approval.
    """

    if tool_name not in TOOL_MAP:
        raise ValueError(
            f"Unknown tool: {tool_name}"
        )

    if (
        is_dangerous_action(tool_name)
        and approval_status != "approved"
    ):
        raise PermissionError(
            approval_message(tool_name)
        )

    tool = TOOL_MAP[tool_name]

    return tool.invoke(arguments)


# ============================================================
# TOOL USE POLICY
# ============================================================

INFORMATIONAL_PHRASES = (
    "give me", "tell me", "what are", "what is", "explain",
    "how do i", "how to", "commands", "command list", "cheat sheet",
    "tutorial", "guide", "difference between", "compare", "learn",
    "beginner", "important commands",
)


def is_informational_request(message: str) -> bool:
    """Return True for knowledge-only requests."""
    text = " ".join(message.lower().split())
    return any(phrase in text for phrase in INFORMATIONAL_PHRASES)


TOOL_USAGE_INSTRUCTION = """
TOOL EXECUTION POLICY:

- The CURRENT USER REQUEST is authoritative.
- Never execute a tool because of a previous conversation message.
- Never reuse a container name, pod name, command, resource, or action
  from conversation history unless the current user explicitly refers to it.
- Use a DevOps tool only when the current request explicitly asks you
  to inspect, check, run, execute, verify, list, diagnose using live
  system information, or perform an operation.
- If the user asks for an explanation, tutorial, command list, examples,
  concepts, or general troubleshooting guidance, answer directly and
  do not call a tool.
- Match tools to the current technology.
- Never invent resource names such as "test-container".
- Never claim a tool was executed unless it actually ran.
"""


def build_system_prompt(memory_text: str, context: str) -> str:
    return (
        DEVOPS_SYSTEM_PROMPT
        + "\n\n"
        + TOOL_USAGE_INSTRUCTION
        + "\n\n"
        + MEMORY_INSTRUCTION.format(memory=memory_text)
        + "\n\n"
        + RAG_INSTRUCTION.format(
            context=context if context else "No relevant knowledge retrieved."
        )
    )


# ============================================================
# STREAMING HELPERS
# ============================================================

def sse_event(event: str, data) -> str:
    """
    Format one Server-Sent Event (SSE) message.
    """
    if not isinstance(data, str):
        data = json.dumps(data, ensure_ascii=False)

    return (
        f"event: {event}\n"
        f"data: {data}\n\n"
    )


# ============================================================
# STREAMING CHAT
# ============================================================

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming version of /chat.

    SSE events:
      status   -> processing/tool information
      approval -> dangerous action needs approval
      token    -> incremental AI response text
      done     -> final response metadata
      error    -> request failure

    The original /chat endpoint remains available as a
    non-streaming fallback.
    """

    project_id = request.project_id
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    # Verify the project before opening the stream.
    db = SessionLocal()

    try:
        project = (
            db.query(Project)
            .filter(Project.id == project_id)
            .first()
        )

        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        memory = get_project_memory(
            db=db,
            project_id=project_id,
            limit=10,
        )

    finally:
        db.close()

    memory_text = format_memory(memory)

    context = retrieve_context(
        user_message,
        k=3,
    )

    system_prompt = build_system_prompt(memory_text, context)

    messages = [
        SystemMessage(content=system_prompt)
    ]

    for item in memory:
        previous_user = item.get("user")
        previous_assistant = item.get("assistant")

        if previous_user:
            messages.append(
                HumanMessage(content=previous_user)
            )

        if previous_assistant:
            messages.append(
                AIMessage(content=previous_assistant)
            )

    messages.append(
        HumanMessage(content=user_message)
    )

    use_tools = not is_informational_request(user_message)
    model = llm.bind_tools(DEVOPS_TOOLS) if use_tools else llm

    async def event_generator():
        tool_used = False

        try:
            yield sse_event(
                "status",
                {
                    "message": "Analyzing your request..."
                },
            )

            max_steps = 5

            # -----------------------------------------------
            # Agent/tool loop
            # -----------------------------------------------
            for step in range(max_steps):
                yield sse_event(
                    "status",
                    {
                        "message": (
                            "Thinking"
                            + ("..." if step == 0 else f" (step {step + 1})...")
                        )
                    },
                )

                response = await model.ainvoke(messages)
                messages.append(response)

                tool_calls = getattr(
                    response,
                    "tool_calls",
                    []
                )

                if not tool_calls:
                    break

                tool_used = True

                for tool_call in tool_calls:
                    tool_name = get_tool_name(tool_call)
                    arguments = get_tool_arguments(tool_call)

                    if not tool_name:
                        continue

                    yield sse_event(
                        "tool_start",
                        {
                            "tool": tool_name,
                            "arguments": arguments,
                        },
                    )

                    if tool_name not in TOOL_MAP:
                        tool_result = f"Unknown tool: {tool_name}"

                        create_audit_log(
                            action=tool_name,
                            tool=tool_name,
                            arguments=arguments,
                            status="unknown_tool",
                            result=tool_result,
                            project_id=project_id,
                        )

                        messages.append(
                            ToolMessage(
                                content=tool_result,
                                tool_call_id=tool_call["id"],
                            )
                        )

                        yield sse_event(
                            "tool_result",
                            {
                                "tool": tool_name,
                                "success": False,
                                "result": tool_result,
                            },
                        )
                        continue

                    # ---------------------------------------
                    # Dangerous action -> approval
                    # ---------------------------------------
                    if is_dangerous_action(tool_name):
                        approval = create_approval(
                            project_id=project_id,
                            action_name=tool_name,
                            description=(
                                f"AI requested execution of "
                                f"'{tool_name}'."
                            ),
                            tool_name=tool_name,
                            arguments=arguments,
                        )

                        create_audit_log(
                            action=tool_name,
                            tool=tool_name,
                            arguments=arguments,
                            status="approval_required",
                            result=(
                                "Dangerous action requires "
                                "explicit user approval."
                            ),
                            project_id=project_id,
                            approval_id=approval["id"],
                        )

                        yield sse_event(
                            "approval",
                            {
                                "approval_required": True,
                                "approval": approval,
                                "message": approval_message(tool_name),
                            },
                        )
                        return

                    # ---------------------------------------
                    # Safe tool
                    # ---------------------------------------
                    try:
                        tool_result = execute_tool_call(
                            tool_name=tool_name,
                            arguments=arguments,
                        )

                        serialized_result = serialize_tool_result(
                            tool_result
                        )

                        create_audit_log(
                            action=tool_name,
                            tool=tool_name,
                            arguments=arguments,
                            status="success",
                            result=serialized_result,
                            project_id=project_id,
                        )

                        yield sse_event(
                            "tool_result",
                            {
                                "tool": tool_name,
                                "success": True,
                                "result": serialized_result,
                            },
                        )

                    except Exception as e:
                        serialized_result = (
                            "Tool execution failed: "
                            f"{str(e)}"
                        )

                        create_audit_log(
                            action=tool_name,
                            tool=tool_name,
                            arguments=arguments,
                            status="failed",
                            result=serialized_result,
                            project_id=project_id,
                        )

                        yield sse_event(
                            "tool_result",
                            {
                                "tool": tool_name,
                                "success": False,
                                "result": serialized_result,
                            },
                        )

                    messages.append(
                        ToolMessage(
                            content=serialized_result,
                            tool_call_id=tool_call["id"],
                        )
                    )

            else:
                fallback_response = (
                    "I reached the maximum number of "
                    "DevOps tool steps for this request. "
                    "Please break the task into smaller steps."
                )

                db = SessionLocal()
                try:
                    db.add(
                        ChatMessage(
                            project_id=project_id,
                            user_message=user_message,
                            ai_response=fallback_response,
                        )
                    )
                    db.commit()
                finally:
                    db.close()

                for token in [fallback_response]:
                    yield sse_event("token", token)

                yield sse_event(
                    "done",
                    {
                        "success": True,
                        "tool_used": tool_used,
                    },
                )
                return

            # -----------------------------------------------
            # Stream final answer
            # -----------------------------------------------
            yield sse_event(
                "status",
                {
                    "message": (
                        "Generating response..."
                    )
                },
            )

            # Gemini does not allow model prefilling. Make sure
            # the final request ends with a real user message.
            messages.append(
                HumanMessage(
                    content=(
                        "Now provide the final answer to my original "
                        "request using the results above. "
                        "Do not mention this instruction."
                    )
                )
            )

            messages.append(
                HumanMessage(
                    content=(
                        "Now provide the final answer to my original "
                        "request using the relevant information above. "
                        "Do not mention this instruction."
                    )
                )
            )

            full_response = []

            async for chunk in llm.astream(messages):
                text = extract_ai_text(chunk.content)

                if text:
                    full_response.append(text)
                    yield sse_event("token", text)

            ai_response = "".join(full_response).strip()

            if not ai_response:
                ai_response = (
                    "I couldn't generate a response."
                )
                yield sse_event("token", ai_response)

            # -----------------------------------------------
            # Save chat history
            # -----------------------------------------------
            db = SessionLocal()
            try:
                db.add(
                    ChatMessage(
                        project_id=project_id,
                        user_message=user_message,
                        ai_response=ai_response,
                    )
                )
                db.commit()
            finally:
                db.close()

            yield sse_event(
                "done",
                {
                    "success": True,
                    "tool_used": tool_used,
                },
            )

        except Exception as e:
            yield sse_event(
                "error",
                {
                    "message": str(e)
                },
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "name": "AI DevOps Assistant",
        "version": "11.1.2",
        "status": "running",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# PROJECTS
# ============================================================

@app.get("/projects")
def get_projects():
    db = SessionLocal()

    try:
        projects = (
            db.query(Project)
            .order_by(Project.created_at.desc())
            .all()
        )

        return [
            {
                "id": project.id,
                "name": project.name,
                "created_at": (
                    project.created_at.isoformat()
                    if project.created_at
                    else None
                ),
            }
            for project in projects
        ]

    finally:
        db.close()


@app.post("/projects")
def create_project(
    project: ProjectCreate,
):
    name = project.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Project name cannot be empty.",
        )

    db = SessionLocal()

    try:
        existing = (
            db.query(Project)
            .filter(Project.name == name)
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Project already exists.",
            )

        new_project = Project(
            name=name
        )

        db.add(new_project)
        db.commit()
        db.refresh(new_project)

        return {
            "id": new_project.id,
            "name": new_project.name,
            "created_at": (
                new_project.created_at.isoformat()
                if new_project.created_at
                else None
            ),
        }

    finally:
        db.close()


@app.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
):
    db = SessionLocal()

    try:
        project = (
            db.query(Project)
            .filter(Project.id == project_id)
            .first()
        )

        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        db.delete(project)
        db.commit()

        return {
            "success": True,
            "message": "Project deleted successfully.",
        }

    finally:
        db.close()


# ============================================================
# PROJECT MESSAGES
# ============================================================

@app.get("/projects/{project_id}/messages")
def get_project_messages(
    project_id: int,
):
    db = SessionLocal()

    try:
        project = (
            db.query(Project)
            .filter(Project.id == project_id)
            .first()
        )

        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        messages = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.project_id == project_id
            )
            .order_by(
                ChatMessage.created_at.asc()
            )
            .all()
        )

        return [
            {
                "id": message.id,
                "user_message": message.user_message,
                "ai_response": message.ai_response,
                "created_at": (
                    message.created_at.isoformat()
                    if message.created_at
                    else None
                ),
            }
            for message in messages
        ]

    finally:
        db.close()


# ============================================================
# CHAT
# ============================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
):
    project_id = request.project_id

    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Verify project
        # ----------------------------------------------------

        project = (
            db.query(Project)
            .filter(Project.id == project_id)
            .first()
        )

        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        # ----------------------------------------------------
        # Conversation Memory
        # ----------------------------------------------------

        memory = get_project_memory(
            db=db,
            project_id=project_id,
            limit=10,
        )

        memory_text = format_memory(
            memory
        )

        # ----------------------------------------------------
        # RAG
        # ----------------------------------------------------

        context = retrieve_context(
            user_message,
            k=3,
        )

        # ----------------------------------------------------
        # System Prompt
        # ----------------------------------------------------

        system_prompt = build_system_prompt(memory_text, context)

        # ----------------------------------------------------
        # LLM Messages
        # ----------------------------------------------------

        messages = [
            SystemMessage(
                content=system_prompt
            )
        ]

        # Add previous conversation
        for item in memory:

            previous_user = item.get(
                "user"
            )

            previous_assistant = item.get(
                "assistant"
            )

            if previous_user:
                messages.append(
                    HumanMessage(
                        content=previous_user
                    )
                )

            if previous_assistant:
                messages.append(
                    AIMessage(
                        content=previous_assistant
                    )
                )

        # Current user message
        messages.append(
            HumanMessage(
                content=user_message
            )
        )

        # ----------------------------------------------------
        # Bind DevOps Tools
        # ----------------------------------------------------

        use_tools = not is_informational_request(user_message)
        model = llm.bind_tools(DEVOPS_TOOLS) if use_tools else llm

        max_steps = 5

        # ----------------------------------------------------
        # Agent Loop
        # ----------------------------------------------------

        for step in range(max_steps):

            response = model.invoke(
                messages
            )

            messages.append(
                response
            )

            tool_calls = getattr(
                response,
                "tool_calls",
                []
            )

            # ------------------------------------------------
            # No Tool Call
            # ------------------------------------------------

            if not tool_calls:

                ai_response = extract_ai_text(
                    response.content
                )

                if not ai_response:
                    ai_response = (
                        "I couldn't generate "
                        "a response."
                    )

                chat_message = ChatMessage(
                    project_id=project_id,
                    user_message=user_message,
                    ai_response=ai_response,
                )

                db.add(chat_message)
                db.commit()

                return {
                    "success": True,
                    "response": ai_response,
                    "tool_used": False,
                }

            # ------------------------------------------------
            # Process Tool Calls
            # ------------------------------------------------

            for tool_call in tool_calls:

                tool_name = get_tool_name(
                    tool_call
                )

                arguments = get_tool_arguments(
                    tool_call
                )

                if not tool_name:
                    continue

                # --------------------------------------------
                # Unknown Tool
                # --------------------------------------------

                if tool_name not in TOOL_MAP:

                    tool_result = (
                        f"Unknown tool: "
                        f"{tool_name}"
                    )

                    messages.append(
                        ToolMessage(
                            content=tool_result,
                            tool_call_id=(
                                tool_call["id"]
                            ),
                        )
                    )

                    continue

                # --------------------------------------------
                # Dangerous Tool
                # --------------------------------------------

                if is_dangerous_action(
                    tool_name
                ):

                    approval = create_approval(
                        project_id=project_id,
                        action_name=tool_name,
                        description=(
                            f"AI requested "
                            f"execution of "
                            f"'{tool_name}'."
                        ),
                        tool_name=tool_name,
                        arguments=arguments,
                    )

                    # Audit approval request
                    create_audit_log(
                        action=tool_name,
                        tool=tool_name,
                        arguments=arguments,
                        status=(
                            "approval_required"
                        ),
                        result=(
                            "Dangerous action "
                            "requires explicit "
                            "user approval."
                        ),
                        project_id=project_id,
                        approval_id=(
                            approval["id"]
                        ),
                    )

                    return {
                        "success": True,
                        "approval_required": True,
                        "approval": approval,
                        "message": (
                            approval_message(
                                tool_name
                            )
                        ),
                    }

                # --------------------------------------------
                # Safe Tool
                # --------------------------------------------

                try:

                    tool_result = execute_tool_call(
                        tool_name=tool_name,
                        arguments=arguments,
                    )

                    serialized_result = (
                        serialize_tool_result(
                            tool_result
                        )
                    )

                    # Audit successful tool
                    create_audit_log(
                        action=tool_name,
                        tool=tool_name,
                        arguments=arguments,
                        status="success",
                        result=(
                            serialized_result
                        ),
                        project_id=project_id,
                    )

                except Exception as e:

                    serialized_result = (
                        "Tool execution failed: "
                        f"{str(e)}"
                    )

                    # Audit failed tool
                    create_audit_log(
                        action=tool_name,
                        tool=tool_name,
                        arguments=arguments,
                        status="failed",
                        result=(
                            serialized_result
                        ),
                        project_id=project_id,
                    )

                # Send result back to LLM
                messages.append(
                    ToolMessage(
                        content=serialized_result,
                        tool_call_id=(
                            tool_call["id"]
                        ),
                    )
                )

        # ----------------------------------------------------
        # Maximum Agent Steps
        # ----------------------------------------------------

        fallback_response = (
            "I reached the maximum number "
            "of DevOps tool steps for this "
            "request. Please break the task "
            "into smaller steps."
        )

        chat_message = ChatMessage(
            project_id=project_id,
            user_message=user_message,
            ai_response=fallback_response,
        )

        db.add(chat_message)
        db.commit()

        return {
            "success": True,
            "response": fallback_response,
            "tool_used": True,
        }

    finally:
        db.close()


# ============================================================
# GET APPROVAL
# ============================================================

@app.get("/approval/{approval_id}")
def get_approval_request(
    approval_id: str,
):
    approval = get_approval(
        approval_id
    )

    if not approval:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found.",
        )

    return approval


# ============================================================
# APPROVE ACTION
# ============================================================

@app.post("/approve/{approval_id}")
def approve_approval(
    approval_id: str,
):
    approval = approve_action(
        approval_id
    )

    if not approval:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found.",
        )

    # Audit approval
    create_audit_log(
        action=approval["action"],
        tool=approval["tool"],
        arguments=approval["arguments"],
        status=(
            "approved"
            if approval["status"] == "approved"
            else approval["status"]
        ),
        result=(
            "User approved the requested action."
            if approval["status"] == "approved"
            else (
                f"Approval status: "
                f"{approval['status']}"
            )
        ),
        project_id=approval[
            "project_id"
        ],
        approval_id=approval_id,
    )

    return {
        "success": True,
        "approval": approval,
    }


# ============================================================
# REJECT ACTION
# ============================================================

@app.post("/reject/{approval_id}")
def reject_approval(
    approval_id: str,
):
    approval = reject_action(
        approval_id
    )

    if not approval:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found.",
        )

    # Audit rejection
    create_audit_log(
        action=approval["action"],
        tool=approval["tool"],
        arguments=approval["arguments"],
        status=(
            "rejected"
            if approval["status"] == "rejected"
            else approval["status"]
        ),
        result=(
            "User rejected the requested action."
            if approval["status"] == "rejected"
            else (
                f"Approval status: "
                f"{approval['status']}"
            )
        ),
        project_id=approval[
            "project_id"
        ],
        approval_id=approval_id,
    )

    return {
        "success": True,
        "approval": approval,
    }


# ============================================================
# EXECUTE APPROVED ACTION
# ============================================================

@app.post(
    "/execute-approval/{approval_id}"
)
def execute_approval(
    approval_id: str,
    request: ApprovalExecutionRequest,
):

    # --------------------------------------------------------
    # Get Approval
    # --------------------------------------------------------

    approval = get_approval(
        approval_id
    )

    if not approval:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found.",
        )

    # --------------------------------------------------------
    # Project Binding
    # --------------------------------------------------------

    project_id = request.project_id

    if approval["project_id"] != project_id:

        create_audit_log(
            action=approval["action"],
            tool=approval["tool"],
            arguments=approval["arguments"],
            status="project_mismatch",
            result=(
                "Execution rejected because "
                "the supplied project does not "
                "match the approval project."
            ),
            project_id=project_id,
            approval_id=approval_id,
        )

        raise HTTPException(
            status_code=403,
            detail=(
                "This approval does not belong "
                "to the specified project."
            ),
        )

    # --------------------------------------------------------
    # Approval Validation
    # --------------------------------------------------------

    can_execute, error_message = (
        can_execute_approval(
            approval_id=approval_id,
            project_id=project_id,
        )
    )

    if not can_execute:

        create_audit_log(
            action=approval["action"],
            tool=approval["tool"],
            arguments=approval["arguments"],
            status="execution_blocked",
            result=error_message,
            project_id=project_id,
            approval_id=approval_id,
        )

        raise HTTPException(
            status_code=400,
            detail=error_message,
        )

    # --------------------------------------------------------
    # Tool Information
    # --------------------------------------------------------

    tool_name = approval["tool"]

    arguments = approval["arguments"]

    if tool_name not in TOOL_MAP:

        create_audit_log(
            action=tool_name,
            tool=tool_name,
            arguments=arguments,
            status="unknown_tool",
            result=(
                f"Unknown tool: {tool_name}"
            ),
            project_id=project_id,
            approval_id=approval_id,
        )

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown tool: {tool_name}"
            ),
        )

    # --------------------------------------------------------
    # Execute Tool
    # --------------------------------------------------------

    try:

        result = execute_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            approval_status="approved",
        )

        serialized_result = (
            serialize_tool_result(
                result
            )
        )

        # -----------------------------------------------
        # Audit Successful Execution
        # -----------------------------------------------

        create_audit_log(
            action=tool_name,
            tool=tool_name,
            arguments=arguments,
            status=(
                "approved_and_executed"
            ),
            result=serialized_result,
            project_id=project_id,
            approval_id=approval_id,
        )

        # -----------------------------------------------
        # Mark Approval Executed
        # -----------------------------------------------

        updated_approval = mark_executed(
            approval_id
        )

        return {
            "success": True,
            "approval": updated_approval,
            "tool": tool_name,
            "arguments": arguments,
            "result": serialized_result,
        }

    except Exception as e:

        error_message = str(e)

        # -----------------------------------------------
        # Audit Failed Execution
        # -----------------------------------------------

        create_audit_log(
            action=tool_name,
            tool=tool_name,
            arguments=arguments,
            status="execution_failed",
            result=error_message,
            project_id=project_id,
            approval_id=approval_id,
        )

        return {
            "success": False,
            "approval": approval,
            "tool": tool_name,
            "arguments": arguments,
            "error": error_message,
        }


# ============================================================
# AUDIT LOGS
# ============================================================

@app.get("/audit-logs")
def audit_logs(
    project_id: int | None = None,
    limit: int = 100,
):

    if limit < 1 or limit > 500:

        raise HTTPException(
            status_code=400,
            detail=(
                "Limit must be between "
                "1 and 500."
            ),
        )

    logs = get_audit_logs(
        project_id=project_id,
        limit=limit,
    )

    return {
        "success": True,
        "count": len(logs),
        "logs": logs,
    }
