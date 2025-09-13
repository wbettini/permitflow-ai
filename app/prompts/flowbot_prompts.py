"""
🧠 FlowBot Prompt Builder

Constructs system prompts by merging FlowBot's core role with avatar-specific personality traits.
Used for persona-driven LLM initialization, fallback orchestration, and preview harnesses.
"""

import json
from pathlib import Path

# 📁 Path to config folder
DB_PATH = Path(__file__).parent.parent / "permitFlowDb"

# -------------------------------------------------------------------------
# 📦 Config Loaders
# -------------------------------------------------------------------------

def load_config(filename: str) -> dict:
    """
    Load a JSON config file from permitFlowDb.
    """
    with open(DB_PATH / filename, "r", encoding="utf-8") as f:
        return json.load(f)

# 🔄 Load persona definitions, avatar mappings, and system role prompt
PERSONAS = load_config("personas.json")      # e.g. "mentor", "grumpy", "cheerful"
AVATAR_MAP = load_config("avatars.json")     # e.g. "Alexandra" → "mentor"
SYSTEM_PROMPTS = load_config("system_prompts.json")  # e.g. flowbot_role string

# -------------------------------------------------------------------------
# 🧾 Persona-Aware Prompt Builder
# -------------------------------------------------------------------------

def build_flowbot_system_prompt(persona_key: str) -> str:
    """
    Build a system prompt for the LLM based on the selected persona.

    Args:
        persona_key: The persona name (e.g., "mentor", "grumpy").

    Returns:
        A system prompt string describing the bot's behavior and tone.
    """
    persona = PERSONAS.get(persona_key, PERSONAS["default"])
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