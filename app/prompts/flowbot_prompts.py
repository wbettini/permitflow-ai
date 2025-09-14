"""
app/prompts/flowbot_prompts.py

Responsible for:
- Loading system prompt templates from JSON.
- Building persona-aware system prompts for FlowBot.
"""

from pathlib import Path
import json
from typing import Dict

from app.core.persona_config_loader import PERSONAS, AVATAR_MAP
from app.session.persona_store import get_persona_config

# 📁 Path to config folder
DB_PATH = Path(__file__).parent.parent / "permitFlowDb"

# -------------------------------------------------------------------------
# 📦 Config Loader
# -------------------------------------------------------------------------
def load_config(filename: str) -> Dict:
    """
    Load a JSON config file from permitFlowDb.

    Args:
        filename: Name of the JSON file to load.

    Returns:
        dict: Parsed JSON content.
    """
    with open(DB_PATH / filename, "r", encoding="utf-8") as f:
        return json.load(f)

# 🔄 Load system role prompt definitions
SYSTEM_PROMPTS = load_config("system_prompts.json")

# -------------------------------------------------------------------------
# 🧾 Persona-Aware Prompt Builder
# -------------------------------------------------------------------------
def build_flowbot_system_prompt(persona_key: str) -> str:
    """
    Build a system prompt for the LLM based on the selected persona.

    Args:
        persona_key: The persona name (e.g., "mentor", "grumpy").

    Returns:
        str: A system prompt string describing the bot's behavior and tone.
    """
    persona = get_persona_config(persona_key)
    tone = persona.get("tone", "friendly")
    demeanor = persona.get("demeanor", "")
    style = persona.get("style", "")

    return (
        f"You are FlowBot, a conversational agent with the '{persona_key}' persona.\n"
        f"Tone: {tone}\n"
        f"Demeanor: {demeanor}\n"
        f"Style: {style}\n"
        "Respond with clarity, personality, and consistency. Stay in character at all times."
    )