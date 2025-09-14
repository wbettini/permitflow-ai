from typing import List, Dict
from app.core.logger import logger
from app.core.config import SITE_PROPERTIES
from app.session.memory_manager import get_or_create_memory

MAX_CONTEXT_TURNS = SITE_PROPERTIES.get("MAX_CONTEXT_TURNS", 5)  # fallback to 5

def get_context_history(session_id: str, limit: int = MAX_CONTEXT_TURNS) -> List[Dict[str, str]]:
    """
    Retrieve the last N exchanges from LangChain memory.

    Args:
        session_id: The FlowBot session identifier.
        limit: Max number of turns to return.

    Returns:
        A list of message dicts in chronological order.
    """
    try:
        memory = get_or_create_memory(session_id)
        messages = memory.chat_memory.messages[-limit:]
        logger.debug(f"[Context Retrieved] session_id={session_id} | turns={len(messages)}")
        return [{"role": msg.type, "content": msg.content} for msg in messages]
    except Exception as e:
        logger.warning(f"[Context Retrieval Failed] session_id={session_id} | Reason: {e}", exc_info=True)
        return []

def save_to_context_history(session_id: str, role: str, content: str):
    """
    Append a new message to LangChain memory.

    Args:
        session_id: The FlowBot session identifier.
        role: "user" or "bot"
        content: Message text
    """
    try:
        memory = get_or_create_memory(session_id)
        if role == "user":
            memory.chat_memory.add_user_message(content)
        elif role == "bot":
            memory.chat_memory.add_ai_message(content)
        else:
            logger.warning(f"[Context Save Skipped] Unknown role={role}")
        logger.debug(f"[Context Saved] session_id={session_id} | role={role} | content={content}")
    except Exception as e:
        logger.warning(f"[Context Save Failed] session_id={session_id} | Reason: {e}", exc_info=True)