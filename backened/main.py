from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.database import engine, Base, SessionLocal
from database.models import ChatMessage, Project

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
)

from ai.llm import llm
from ai.prompts import DEVOPS_SYSTEM_PROMPT
from ai.rag import retrieve_context
from tools.registry import DOCKER_TOOLS


# ==================================================
# DATABASE
# ==================================================

Base.metadata.create_all(bind=engine)


def create_default_project():

    db = SessionLocal()

    try:

        existing_project = (
            db.query(Project)
            .filter(
                Project.name == "DevOps Assistant"
            )
            .first()
        )

        if not existing_project:

            default_project = Project(
                name="DevOps Assistant"
            )

            db.add(default_project)
            db.commit()

    finally:

        db.close()


create_default_project()


# ==================================================
# FASTAPI
# ==================================================

app = FastAPI(
    title="AI DevOps Assistant",
    description="GenAI DevOps Assistant using Gemini, LangChain, RAG and Docker tools",
    version="3.0.0"
)


# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# DATABASE SESSION
# ==================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ==================================================
# REQUEST MODELS
# ==================================================

class ProjectRequest(BaseModel):
    name: str


class ChatRequest(BaseModel):
    message: str
    project_id: int


# ==================================================
# RESPONSE TEXT HELPER
# ==================================================

def extract_response_text(content):

    if isinstance(content, str):
        return content

    if isinstance(content, list):

        text_parts = []

        for item in content:

            if isinstance(item, dict):

                if item.get("type") == "text":

                    text_parts.append(
                        item.get("text", "")
                    )

            elif isinstance(item, str):

                text_parts.append(item)

        return "\n".join(text_parts)

    return str(content)


# ==================================================
# ROOT
# ==================================================

@app.get("/")
def root():

    return {
        "message": "AI DevOps Assistant API is running!"
    }


# ==================================================
# HEALTH
# ==================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "database": "connected",
        "ai": "Gemini + LangChain",
        "rag": "ChromaDB + HuggingFace",
        "tools": "Docker"
    }


# ==================================================
# PROJECTS
# ==================================================

@app.get("/projects")
def get_projects(
    db: Session = Depends(get_db)
):

    projects = (
        db.query(Project)
        .order_by(Project.id.asc())
        .all()
    )

    return [
        {
            "id": project.id,
            "name": project.name,
            "created_at": project.created_at
        }
        for project in projects
    ]


@app.post("/projects")
def create_project(
    project: ProjectRequest,
    db: Session = Depends(get_db)
):

    project_name = project.name.strip()

    if not project_name:

        return {
            "error": "Project name cannot be empty"
        }

    existing_project = (
        db.query(Project)
        .filter(
            Project.name == project_name
        )
        .first()
    )

    if existing_project:

        return {
            "error": "Project already exists"
        }

    new_project = Project(
        name=project_name
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return {
        "id": new_project.id,
        "name": new_project.name,
        "created_at": new_project.created_at
    }


@app.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db)
):

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id
        )
        .first()
    )

    if not project:

        return {
            "error": "Project not found"
        }

    project_count = (
        db.query(Project).count()
    )

    if project_count == 1:

        return {
            "error": "You must keep at least one project"
        }

    db.delete(project)
    db.commit()

    return {
        "message": "Project deleted successfully"
    }


# ==================================================
# CHAT HISTORY
# ==================================================

@app.get("/projects/{project_id}/chats")
def get_project_chats(
    project_id: int,
    db: Session = Depends(get_db)
):

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id
        )
        .first()
    )

    if not project:

        return {
            "error": "Project not found"
        }

    chats = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.project_id == project_id
        )
        .order_by(
            ChatMessage.id.asc()
        )
        .all()
    )

    return [
        {
            "id": chat.id,
            "project_id": chat.project_id,
            "user_message": chat.user_message,
            "ai_response": chat.ai_response,
            "created_at": chat.created_at
        }
        for chat in chats
    ]


# ==================================================
# TOOL EXECUTION
# ==================================================

def execute_tool_call(tool_call):

    tool_name = tool_call["name"]

    tool_args = tool_call.get(
        "args",
        {}
    )

    allowed_tools = {
        tool.name: tool
        for tool in DOCKER_TOOLS
    }

    tool = allowed_tools.get(
        tool_name
    )

    if not tool:

        return f"Tool '{tool_name}' is not allowed."

    try:

        result = tool.invoke(
            tool_args
        )

        return str(result)

    except Exception as e:

        return f"Tool execution failed: {str(e)}"


# ==================================================
# CHAT
# ==================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):

    # ----------------------------------------------
    # Find project
    # ----------------------------------------------

    project = (
        db.query(Project)
        .filter(
            Project.id == request.project_id
        )
        .first()
    )

    if not project:

        return {
            "error": "Project not found"
        }


    # ----------------------------------------------
    # RAG
    # ----------------------------------------------

    try:

        rag_context = retrieve_context(
            request.message,
            k=4
        )

    except Exception as e:

        print(
            f"RAG retrieval error: {e}"
        )

        rag_context = ""


    # ----------------------------------------------
    # System prompt
    # ----------------------------------------------

    system_prompt = f"""
{DEVOPS_SYSTEM_PROMPT}

You are an AI DevOps assistant with access to
safe, read-only Docker diagnostic tools.

Available tools:

- check_docker_version
- check_docker_status
- get_docker_containers
- get_docker_images

Rules:

1. Use Docker tools when the user asks about the
   actual Docker installation or Docker resources
   on their computer.

2. Never claim a command was executed unless the
   tool actually executed it.

3. Never execute arbitrary shell commands.

4. Never perform destructive Docker operations.

5. After receiving a tool result, clearly explain
   that result to the user.

6. If a tool returns no containers or images,
   explicitly tell the user that none were found.

==================================================
RAG KNOWLEDGE
==================================================

{rag_context}

==================================================
"""


    # ----------------------------------------------
    # Chat history
    # ----------------------------------------------

    previous_chats = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.project_id == project.id
        )
        .order_by(
            ChatMessage.id.desc()
        )
        .limit(10)
        .all()
    )

    previous_chats.reverse()


    # ----------------------------------------------
    # Build messages
    # ----------------------------------------------

    messages = [
        SystemMessage(
            content=system_prompt
        )
    ]


    for previous_chat in previous_chats:

        messages.append(
            HumanMessage(
                content=previous_chat.user_message
            )
        )

        messages.append(
            AIMessage(
                content=previous_chat.ai_response
            )
        )


    messages.append(
        HumanMessage(
            content=request.message
        )
    )


    # ----------------------------------------------
    # Bind Docker tools
    # ----------------------------------------------

    llm_with_tools = llm.bind_tools(
        DOCKER_TOOLS
    )


    # ----------------------------------------------
    # First Gemini call
    # ----------------------------------------------

    response = llm_with_tools.invoke(
        messages
    )


    tools_used = []


    # ----------------------------------------------
    # Tool calling
    # ----------------------------------------------

    if response.tool_calls:

        messages.append(
            response
        )


        for tool_call in response.tool_calls:

            tool_name = tool_call["name"]

            print(
                f"Executing tool: {tool_name}"
            )

            tool_result = execute_tool_call(
                tool_call
            )

            print(
                f"Tool result: {tool_result}"
            )

            tools_used.append(
                tool_name
            )

            messages.append(
                ToolMessage(
                    content=tool_result,
                    tool_call_id=tool_call["id"],
                    name=tool_name
                )
            )


        # ------------------------------------------
        # Second Gemini call
        # ------------------------------------------

        final_response = llm_with_tools.invoke(
            messages
        )


        print(
            f"Final Gemini response: {final_response.content}"
        )


        ai_response = extract_response_text(
            final_response.content
        )


        # ------------------------------------------
        # Safety fallback
        # ------------------------------------------

        if not ai_response.strip():

            tool_outputs = []

            for message in messages:

                if isinstance(
                    message,
                    ToolMessage
                ):

                    tool_outputs.append(
                        str(message.content)
                    )

            if tool_outputs:

                ai_response = (
                    "Here is the result from Docker:\n\n"
                    + "\n\n".join(tool_outputs)
                )

            else:

                ai_response = (
                    "The Docker tool executed successfully, "
                    "but no result was returned."
                )


    else:

        ai_response = extract_response_text(
            response.content
        )


    # ----------------------------------------------
    # Save conversation
    # ----------------------------------------------

    chat_message = ChatMessage(
        project_id=project.id,
        user_message=request.message,
        ai_response=ai_response
    )

    db.add(chat_message)

    db.commit()

    db.refresh(chat_message)


    # ----------------------------------------------
    # Return
    # ----------------------------------------------

    return {
        "message": request.message,
        "response": ai_response,
        "chat_id": chat_message.id,
        "project_id": project.id,
        "project_name": project.name,
        "rag_used": bool(rag_context),
        "tools_used": tools_used
    }
# ==================================================
# CHAT
# ==================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):

    # ----------------------------------------------
    # Find project
    # ----------------------------------------------

    project = (
        db.query(Project)
        .filter(
            Project.id == request.project_id
        )
        .first()
    )

    if not project:

        return {
            "error": "Project not found"
        }


    # ----------------------------------------------
    # RAG
    # ----------------------------------------------

    try:

        rag_context = retrieve_context(
            request.message,
            k=4
        )

    except Exception as e:

        print(
            f"RAG retrieval error: {e}"
        )

        rag_context = ""


    # ----------------------------------------------
    # System prompt
    # ----------------------------------------------

    if rag_context:

        system_prompt = f"""
{DEVOPS_SYSTEM_PROMPT}

==================================================
RELEVANT KNOWLEDGE BASE
==================================================

{rag_context}

==================================================

Use this knowledge when relevant.

You also have access to safe, read-only Docker
diagnostic tools.

Available Docker tools can:

- Check Docker version
- Check Docker Engine status
- List containers
- List images

Never claim that a Docker command was executed unless
you actually called one of the available tools.

Never execute arbitrary shell commands.

Never use destructive Docker operations.
"""

    else:

        system_prompt = f"""
{DEVOPS_SYSTEM_PROMPT}

You have access to safe, read-only Docker diagnostic
tools.

Available Docker tools can:

- Check Docker version
- Check Docker Engine status
- List containers
- List images

Never claim that a Docker command was executed unless
you actually called one of the available tools.

Never execute arbitrary shell commands.

Never use destructive Docker operations.
"""


    # ----------------------------------------------
    # Get previous chats
    # ----------------------------------------------

    previous_chats = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.project_id == project.id
        )
        .order_by(
            ChatMessage.id.desc()
        )
        .limit(10)
        .all()
    )

    previous_chats.reverse()


    # ----------------------------------------------
    # Build messages
    # ----------------------------------------------

    messages = [
        SystemMessage(
            content=system_prompt
        )
    ]


    for previous_chat in previous_chats:

        messages.append(
            HumanMessage(
                content=previous_chat.user_message
            )
        )

        messages.append(
            AIMessage(
                content=previous_chat.ai_response
            )
        )


    messages.append(
        HumanMessage(
            content=request.message
        )
    )


    # ----------------------------------------------
    # Bind tools
    # ----------------------------------------------

    llm_with_tools = llm.bind_tools(
        DOCKER_TOOLS
    )


    # ----------------------------------------------
    # First Gemini call
    # ----------------------------------------------

    response = llm_with_tools.invoke(
        messages
    )


    # ----------------------------------------------
    # Execute requested tools
    # ----------------------------------------------

    if response.tool_calls:

        messages.append(
            response
        )


        for tool_call in response.tool_calls:

            print(
                f"Executing tool: {tool_call['name']}"
            )

            tool_result = execute_tool_call(
                tool_call
            )

            messages.append(
                ToolMessage(
                    content=tool_result,
                    tool_call_id=tool_call["id"]
                )
            )


        # ------------------------------------------
        # Gemini final response
        # ------------------------------------------

        final_response = llm_with_tools.invoke(
            messages
        )

        ai_response = extract_response_text(
            final_response.content
        )

        tools_used = [
            tool_call["name"]
            for tool_call in response.tool_calls
        ]

    else:

        ai_response = extract_response_text(
            response.content
        )

        tools_used = []


    # ----------------------------------------------
    # Save chat
    # ----------------------------------------------

    chat_message = ChatMessage(
        project_id=project.id,
        user_message=request.message,
        ai_response=ai_response
    )

    db.add(chat_message)
    db.commit()
    db.refresh(chat_message)


    # ----------------------------------------------
    # Return
    # ----------------------------------------------

    return {
        "message": request.message,
        "response": ai_response,
        "chat_id": chat_message.id,
        "project_id": project.id,
        "project_name": project.name,
        "rag_used": bool(rag_context),
        "tools_used": tools_used
    }