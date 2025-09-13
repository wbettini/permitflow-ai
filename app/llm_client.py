from app.langchain_config import get_llm
from app.prompts.flowbot_prompts import build_flowbot_system_prompt
from app.core.logger import logger


async def validate_with_llm(persona_key: str, style: str, user_message: str, candidate_reply: str) -> str:
    """
    Validate or polish a candidate reply using the LLM with persona context.

    Args:
        persona_key: The persona name (e.g., "mentor", "grumpy").
        style: The persona's style string from personas.json.
        user_message: The original message from the user.
        candidate_reply: The locally generated reply from FlowBot.

    Returns:
        The validated or rewritten reply from the LLM, or the original if unchanged/failed.
    """
    llm = get_llm(temperature=0.7)
    system_prompt = build_flowbot_system_prompt(persona_key)

    validation_prompt = (
        f"User message: {user_message}\n"
        f"Candidate reply: {candidate_reply}\n\n"
        f"Persona style: {style}\n\n"
        "Task: Ensure the reply is relevant, accurate, and in-character for the persona. "
        "If fine, return unchanged. If not, rewrite it to match the persona's tone, demeanor, and style."
    )

    try:
        logger.debug(f"[LLM Validation] persona={persona_key} | Sending to model for review")
        result = await llm.ainvoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": validation_prompt}
        ])
        validated = result.content.strip()
        logger.debug(f"[LLM Validation] Pre: {candidate_reply} | Post: {validated}")
        return validated or candidate_reply
    except Exception as e:
        logger.warning(f"[LLM Validation Skipped] persona={persona_key} | Reason: {e}")
        return candidate_reply