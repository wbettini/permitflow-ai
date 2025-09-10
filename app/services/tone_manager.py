"""
tone_manager.py — Tone application service for FlowBot.

Responsibilities:
- Apply personality tone transformations to base response text.
- Keep tone definitions centralized for consistency.
- Allow easy expansion with new tones or dynamic tone logic.

Future Changes:
- Load tone definitions from GENERAL_INTENTS or DB.
- Support multi-language tone transformations.
"""

from typing import Literal
from app.core.logger import logger

# ===== Tone Map =====
# Each tone is a callable that transforms the base text.
TONE_MAP = {
    "default": lambda text: text,
    "friendly": lambda text: f"{text} 😊",
    "chippy": lambda text: f"{text} 😉",
    "formal": lambda text: f"{text} I appreciate your inquiry.",
    "playful": lambda text: f"{text} 😏 Just kidding... unless?"
}


# ===== Public API =====
def apply_tone(
    text: str,
    tone: Literal["default", "friendly", "chippy", "formal", "playful"]
) -> str:
    """
    Apply a tone transformation to the given text.

    Args:
        text (str): The base response text.
        tone (str): The tone key to apply.

    Returns:
        str: Tone-adjusted text.
    """
    transformer = TONE_MAP.get(tone.lower(), TONE_MAP["default"])
    result = transformer(text)
    logger.debug(f"[Tone Applied] tone={tone}, result={result}")
    return result