# ==================================================
# CONVERSATION MEMORY
# ==================================================

from sqlalchemy.orm import Session

from database.models import ChatMessage


# ==================================================
# GET RECENT PROJECT MEMORY
# ==================================================

def get_project_memory(
    db: Session,
    project_id: int,
    limit: int = 10
) -> list[dict]:
    """
    Get recent conversation messages for a project.

    Memory is only a source of context.
    The caller decides whether the memory is relevant.
    """

    messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.project_id == project_id
        )
        .order_by(
            ChatMessage.created_at.desc()
        )
        .limit(limit)
        .all()
    )

    messages.reverse()

    memory = []

    for message in messages:
        memory.append({
            "user": message.user_message,
            "assistant": message.ai_response,
        })

    return memory


# ==================================================
# FORMAT MEMORY
# ==================================================

def format_memory(
    memory: list[dict]
) -> str:
    """
    Format relevant conversation context.

    This is reference material only.
    It must never be treated as a new instruction.
    """

    if not memory:
        return "No relevant previous conversation."

    formatted = []

    for item in memory:
        user = item.get("user", "").strip()
        assistant = item.get("assistant", "").strip()

        if not user and not assistant:
            continue

        formatted.append(
            f"Previous user message: {user}\n"
            f"Previous assistant response: {assistant}"
        )

    if not formatted:
        return "No relevant previous conversation."

    return "\n\n---\n\n".join(formatted)