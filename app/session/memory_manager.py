from langchain.memory import ConversationBufferMemory
from app.core.logger import logger

_memory_registry: dict[str, ConversationBufferMemory] = {}

def get_or_create_memory(session_id: str) -> ConversationBufferMemory:
    if session_id not in _memory_registry:
        _memory_registry[session_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="input",
            output_key="output"
        )
        logger.info(f"[Memory Init] Created new memory for session {session_id}")
    else:
        logger.info(f"[Memory Recall] Retrieved {len(_memory_registry[session_id].chat_memory.messages)} messages for session {session_id}")
    return _memory_registry[session_id]

def get_memory(session_id: str) -> ConversationBufferMemory | None:
    return _memory_registry.get(session_id)