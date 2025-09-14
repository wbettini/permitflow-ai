from typing import List, Dict
from app.langchain_config import get_llm
from app.prompts.flowbot_prompts import build_flowbot_system_prompt
from app.core.logger import logger
from app.session.session_context import get_context_history  # hypothetical helper
from app.core.config import SITE_PROPERTIES

MAX_CONTEXT_TURNS = SITE_PROPERTIES.get("MAX_CONTEXT_TURNS", 5)  # last N exchanges to include


async def validate_with_llm(
    session_id: str,
    persona_key: str,
    style: str,
    user_message: str,
    candidate_reply: str
) -> str:
    """
    Validate or polish a candidate reply using the LLM with persona context
    and recent conversation history.

    Args:
        session_id: Current FlowBot session identifier.
        persona_key: The persona name (e.g., "mentor", "grumpy").
        style: The persona's style string from personas.json.
        user_message: The original message from the user.
        candidate_reply: The locally generated reply from FlowBot.

    Returns:
        The validated or rewritten reply from the LLM, or the original if unchanged/failed.
    """
    if not user_message or not candidate_reply:
        logger.debug("[LLM Validation] Skipped — missing user_message or candidate_reply")
        return candidate_reply or ""

    # Load LLM and persona system prompt
    llm = get_llm(temperature=0.7)
    system_prompt = build_flowbot_system_prompt(persona_key)

    # Retrieve last N exchanges for rolling context
    history: List[Dict[str, str]] = get_context_history(session_id, limit=MAX_CONTEXT_TURNS)

    # Build context string from history
    context_str = "\n".join(
        f"{turn['role'].capitalize()}: {turn['content']}" for turn in history
    )

    # Build validation instructions
    validation_prompt = (
        f"Recent conversation:\n{context_str}\n\n"
        f"Latest user message: {user_message}\n"
        f"Candidate reply: {candidate_reply}\n\n"
        f"Persona style: {style}\n\n"
        "Task: Ensure the reply is relevant, accurate, and in-character for the persona. "
        "If fine, return unchanged. If not, rewrite it to match the persona's tone, demeanor, and style."
    )

    try:
        logger.debug(
            f"[LLM Validation] persona={persona_key} | style={style} | "
            f"context_turns={len(history)} | Sending to model for review"
        )

        result = await llm.ainvoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": validation_prompt}
        ])

        validated = (result.content or "").strip()

        logger.debug(
            f"[LLM Validation] Pre: {candidate_reply} | Post: {validated or '[unchanged]'}"
        )

        return validated or candidate_reply

    except Exception as e:
        logger.warning(
            f"[LLM Validation Skipped] persona={persona_key} | Reason: {e}",
            exc_info=True
        )
        return candidate_reply