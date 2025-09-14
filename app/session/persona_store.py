"""
app/session/persona_store.py

Responsible for:
- Resolving an avatar name to its associated persona configuration.
- Providing direct access to persona definitions by key.
"""

from typing import Any, Dict, Optional
from app.core.persona_config_loader import PERSONAS, AVATAR_MAP


def resolve_persona(avatar: str) -> Dict[str, Any]:
    """
    Resolve an avatar name to its persona configuration.

    Args:
        avatar: The avatar name (e.g., "Alexandra", "Robert").

    Returns:
        dict: Persona configuration including style, tone, demeanor, icon, greeting, and fallback.
    """
    # Look up avatar entry in AVATAR_MAP
    avatar_entry: Optional[Any] = AVATAR_MAP.get(avatar)

    # If not found, fall back to the default avatar mapping
    if not avatar_entry:
        avatar_entry = next(
            (v for v in AVATAR_MAP.values()
             if isinstance(v, dict) and v.get("default")),
            {"persona": "default"}
        )

    # Extract persona key and icon depending on entry type
    if isinstance(avatar_entry, dict):
        persona_key = avatar_entry.get("persona", "default")
        icon = avatar_entry.get("icon")
    else:
        persona_key = avatar_entry or "default"
        icon = None

    # Retrieve persona definition from PERSONAS
    persona = PERSONAS.get(persona_key, PERSONAS["default"])

    return {
        "persona_key": persona_key,
        "style": persona.get("style", ""),
        "tone": persona.get("tone", "friendly"),
        "demeanor": persona.get("demeanor", ""),
        "icon": icon,
        "greeting": persona.get("greeting", ""),
        "fallback": persona.get("fallback", "")
    }


def get_persona_config(persona_key: str) -> Dict[str, Any]:
    """
    Retrieve a persona configuration by key.

    Args:
        persona_key: The persona name (e.g., "mentor", "grumpy").

    Returns:
        dict: Persona configuration dictionary.
    """
    return PERSONAS.get(persona_key, PERSONAS["default"])