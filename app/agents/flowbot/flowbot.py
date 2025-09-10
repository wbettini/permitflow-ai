"""
flowbot.py — Core FlowBot conversational agent.

Responsibilities:
- Match user messages to intents using normalization, synonym expansion, and partial matching.
- Generate tone-specific responses with dynamic placeholder substitution.
- Provide proactive greetings on connect.
- Route unmatched inputs to tone-aware failback.
"""

from datetime import datetime
from random import choice
from typing import Any, Dict, List, Optional

from app.core.config import GENERAL_INTENTS
from app.core.logger import logger
from app.utils.text_utils import normalize_text, expand_with_synonyms

# =============================================================================
# FlowBot Class
# =============================================================================

class FlowBot:
    """Conversational agent for handling user messages with tone-aware responses."""

    def __init__(self, user_id: str, tone: str = "default"):
        self.user_id = user_id
        self.tone = tone
        self.intents = GENERAL_INTENTS
        logger.info(f"[FlowBot Init] user_id={self.user_id}, tone={self.tone}")

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    def _placeholder_values(self) -> Dict[str, str]:
        """Generate dynamic placeholder values for response formatting."""
        now = datetime.now()
        return {
            "user_name": self.user_id,
            "time": now.strftime("%-I:%M %p"),
            "date": now.strftime("%B %-d, %Y"),
            "time_of_day": self._get_time_of_day(now.hour),
        }

    @staticmethod
    def _get_time_of_day(hour: int) -> str:
        """Return a human-friendly time of day string."""
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        return "night"

    def _handle_failback(self, message: str) -> str:
        """Return a tone-aware failback response."""
        logger.info(f"[Failback Triggered] user_id={self.user_id}, message={message}")
        failback_intent = self.intents.get("fallback", {})
        responses = failback_intent.get("responses", {})

        if isinstance(responses, dict):
            tone_responses = responses.get(self.tone) or responses.get("formal")
            if isinstance(tone_responses, list) and tone_responses:
                reply = choice(tone_responses).format(**self._placeholder_values())
                logger.info(f"[Failback Response] user_id={self.user_id}, response={reply}")
                return reply
            elif isinstance(tone_responses, str):
                return tone_responses.format(**self._placeholder_values())

        default_reply = "I'm here, but I didn't quite catch that. Could you rephrase?"
        logger.warning(f"[Failback Missing] user_id={self.user_id} — using default: {default_reply}")
        return default_reply

    def _get_greeting(self) -> str:
        """Tone-specific greeting for proactive connect messages."""
        greetings = {
            "chippy": "Hey there! Ready to crush some tollgates?",
            "friendly": "Hi! I'm Alexandra. How can I help you today?",
            "formal": "Greetings. I'm here to assist you with your permit inquiries.",
            "mentor": "Welcome. Let’s move your project forward together.",
            "default": "Hello! How can I assist you?"
        }
        return greetings.get(self.tone, greetings["default"])

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def handle_message(self, message: str) -> str:
        """
        Process an incoming message and return the bot's reply.

        Matching logic:
        - Normalize and expand synonyms for both input and patterns.
        - Allow exact or partial matches.
        - Select tone-specific responses.
        - Fall back to tone-aware failback if no intent matches.
        """
        msg_variants = expand_with_synonyms(message)
        logger.debug(f"[Match Debug] msg_variants={msg_variants}")

        for intent_name, intent_data in self.intents.items():
            for pattern in intent_data.get("patterns", []):
                pattern_variants = expand_with_synonyms(pattern)
                logger.debug(f"[Match Debug] intent={intent_name}, pattern_variants={pattern_variants}")

                if any(
                    mv == pv or mv in pv or pv in mv
                    for mv in msg_variants
                    for pv in pattern_variants
                ):
                    return self._format_response(intent_data)

        return self._handle_failback(message)

    # -------------------------------------------------------------------------
    # Response Formatting
    # -------------------------------------------------------------------------

    def _format_response(self, intent_data: Dict[str, Any]) -> str:
        """Format and return a tone-aware response from intent data."""
        responses = intent_data.get("responses", {})

        if isinstance(responses, dict):
            tone_responses = responses.get(self.tone) or responses.get("formal")
            if isinstance(tone_responses, list) and tone_responses:
                return choice(tone_responses).format(**self._placeholder_values())
            elif isinstance(tone_responses, str):
                return tone_responses.format(**self._placeholder_values())

        elif isinstance(responses, list):
            return choice(responses).format(**self._placeholder_values()) if responses else ""
        elif isinstance(responses, str):
            return responses.format(**self._placeholder_values())

        return ""