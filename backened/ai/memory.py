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
    Get the most recent conversation messages
    for a project.

    The messages are returned in chronological
    order so they can be passed to the LLM.
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


    # Database returns newest first.
    # Reverse so the AI receives oldest → newest.

    messages.reverse()


    memory = []


    for message in messages:

        memory.append({
            "user": message.user_message,
            "assistant": message.ai_response,
        })


    return memory


# ==================================================
# FORMAT MEMORY FOR GEMINI
# ==================================================

def format_memory(
    memory: list[dict]
) -> str:
    """
    Convert conversation history into text
    that can be included in the LLM prompt.
    """

    if not memory:
        return "No previous conversation."


    formatted = []


    for item in memory:

        formatted.append(
            f"User: {item['user']}\n"
            f"Assistant: {item['assistant']}"
        )


    return "\n\n".join(
        formatted
    )