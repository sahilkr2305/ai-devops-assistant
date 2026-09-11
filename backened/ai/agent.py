from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from ai.llm import llm
from tools.registry import DEVOPS_TOOLS


# ============================================================
# TOOL MAP
# ============================================================

TOOL_MAP = {
    tool.name: tool
    for tool in DEVOPS_TOOLS
}


# ============================================================
# AGENT
# ============================================================

def run_agent(
    system_prompt: str,
    user_message: str,
    max_steps: int = 5,
):
    """
    Run the DevOps agent.

    The agent can:
    1. Understand the user's request.
    2. Select a DevOps tool.
    3. Execute the tool.
    4. Analyze the result.
    5. Select another tool if necessary.
    6. Return a final answer.

    Dangerous tools are NOT executed here.
    The existing approval system remains responsible
    for dangerous operations.
    """

    model = llm.bind_tools(
        DEVOPS_TOOLS
    )

    messages = [
        SystemMessage(
            content=system_prompt
        ),
        HumanMessage(
            content=user_message
        ),
    ]

    executed_tools = []

    for step in range(max_steps):

        response = model.invoke(
            messages
        )

        tool_calls = getattr(
            response,
            "tool_calls",
            []
        )

        # ----------------------------------------------------
        # FINAL RESPONSE
        # ----------------------------------------------------

        if not tool_calls:

            return {
                "success": True,
                "response": response,
                "executed_tools": executed_tools,
            }

        # ----------------------------------------------------
        # ADD AI TOOL REQUEST
        # ----------------------------------------------------

        messages.append(
            response
        )

        # ----------------------------------------------------
        # EXECUTE TOOLS
        # ----------------------------------------------------

        for tool_call in tool_calls:

            tool_name = tool_call.get(
                "name"
            )

            arguments = (
                tool_call.get("args")
                or tool_call.get("arguments")
                or {}
            )

            tool = TOOL_MAP.get(
                tool_name
            )

            if not tool:

                tool_result = (
                    f"Tool '{tool_name}' "
                    "is not available."
                )

            else:

                try:

                    result = tool.invoke(
                        arguments
                    )

                    tool_result = str(
                        result
                    )

                    executed_tools.append(
                        {
                            "tool": tool_name,
                            "arguments": arguments,
                            "result": tool_result,
                        }
                    )

                except Exception as e:

                    tool_result = (
                        f"Tool execution failed: "
                        f"{str(e)}"
                    )

            messages.append(
                ToolMessage(
                    content=tool_result,
                    tool_call_id=(
                        tool_call.get("id")
                        or tool_name
                    ),
                )
            )

    # --------------------------------------------------------
    # MAX STEPS REACHED
    # --------------------------------------------------------

    return {
        "success": False,
        "response": (
            "The DevOps agent reached its "
            "maximum number of tool steps."
        ),
        "executed_tools": executed_tools,
    }