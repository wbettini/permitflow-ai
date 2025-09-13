from datetime import datetime
from random import choice
from typing import Any, Dict

from app.core.config import GENERAL_INTENTS
from app.core.logger import logger
from app.utils.text_utils import expand_with_synonyms
from app.prompts.flowbot_prompts import PERSONAS, AVATAR_MAP
from app.llm_client import validate_with_llm


class FlowBot:
    def __init__(self, user_id: str, avatar: str = "default"):
        self.user_id = user_id
        self.avatar = avatar

        avatar_entry = AVATAR_MAP.get(avatar)
        if not avatar_entry:
            avatar_entry = next(
                (v for v in AVATAR_MAP.values()
                 if isinstance(v, dict) and v.get("default")),
                {"persona": "default"}
            )

        if isinstance(avatar_entry, dict):
            self.persona_key = avatar_entry.get("persona", "default")
            self.icon = avatar_entry.get("icon")
        else:
            self.persona_key = avatar_entry or "default"
            self.icon = None

        self.persona = PERSONAS.get(self.persona_key, PERSONAS["default"])
        self.style = self.persona.get("style", "")
        self.greeting_template = self.persona.get(
            "greeting", "Hello! I'm {avatar} ({avatar_icon}). How can I assist you today?"
        )
        self.intents = GENERAL_INTENTS

        logger.info(
            f"[FlowBot Init] user_id={self.user_id}, avatar={self.avatar}, "
            f"persona_key={self.persona_key}, style={self.style}, icon={self.icon}"
        )

    def _placeholder_values(self) -> Dict[str, str]:
        now = datetime.now()
        return {
            "user_name": self.user_id,
            "avatar": self.avatar,
            "avatar_icon": self.icon or "",
            "time": now.strftime("%-I:%M %p"),
            "date": now.strftime("%B %-d, %Y"),
            "time_of_day": self._get_time_of_day(now.hour),
        }

    @staticmethod
    def _get_time_of_day(hour: int) -> str:
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        return "night"

    def _handle_failback(self, message: str) -> str:
        logger.info(f"[Failback Triggered] user_id={self.user_id}, message={message}")
        failback_intent = self.intents.get("fallback", {})
        responses = failback_intent.get("responses", {})

        persona_responses = responses.get(self.persona_key) or responses.get("default")
        if isinstance(persona_responses, list) and persona_responses:
            reply = choice(persona_responses).format(**self._placeholder_values())
            logger.info(f"[Failback Response] user_id={self.user_id}, response={reply}")
            return reply
        elif isinstance(persona_responses, str):
            return persona_responses.format(**self._placeholder_values())

        default_reply = "I'm here, but I didn't quite catch that. Could you rephrase?"
        logger.warning(f"[Failback Missing] user_id={self.user_id} — using default: {default_reply}")
        return default_reply

    def _get_greeting(self) -> str:
        greeting = self.greeting_template.format(**self._placeholder_values())
        logger.debug(f"[Greeting] avatar={self.avatar}, persona={self.persona_key}, greeting={greeting}")
        return greeting

    async def handle_message(self, message: str) -> str:
        candidate_reply = None
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
                    candidate_reply = self._format_response(intent_data)
                    logger.info(f"[Intent Matched] user_id={self.user_id}, intent={intent_name}")
                    break
            if candidate_reply:
                break

        if not candidate_reply:
            candidate_reply = self._handle_failback(message)

        try:
            validated_reply = await validate_with_llm(
                persona_key=self.persona_key,
                style=self.style,
                user_message=message,
                candidate_reply=candidate_reply
            )
            if validated_reply and validated_reply.strip():
                logger.debug(f"[LLM Validation] Pre: {candidate_reply} | Post: {validated_reply}")
                return validated_reply
        except Exception as e:
            logger.warning(f"[LLM Validation Skipped] {e}")

        return candidate_reply

    def _format_response(self, intent_data: Dict[str, Any]) -> str:
        responses = intent_data.get("responses", {})
        persona_responses = responses.get(self.persona_key) or responses.get("default")

        if isinstance(persona_responses, list):
            return choice(persona_responses).format(**self._placeholder_values())
        elif isinstance(persona_responses, str):
            return persona_responses.format(**self._placeholder_values())

        return ""