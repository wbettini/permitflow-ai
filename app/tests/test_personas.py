# app/tests/test_personas.py

"""
🎭 Personality Test Harness for FlowBot

This script runs a simulated workflow output through all defined FlowBot personas
and prints the tone, demeanor, style, and wrapped LLM response for each.

Useful for:
- Previewing avatar voices before wiring into UI
- Validating persona definitions in permitFlowDb/personas.json
- Fine-tuning tone/style for humor, professionalism, or warmth
- Exporting persona previews to JSON for UI or snapshot testing
"""

import json
import argparse
from pathlib import Path

from langchain.prompts import ChatPromptTemplate
from app.langchain_config import get_llm
from app.prompts.flowbot_prompts import build_flowbot_system_prompt

# 📁 Path to config folder
DB_PATH = Path(__file__).parent.parent / "permitFlowDb"

# 📦 Load persona definitions
with open(DB_PATH / "personas.json", "r", encoding="utf-8") as f:
    PERSONAS = json.load(f)

# 🧪 Simulated workflow output (can be swapped for any raw string)
RAW_OUTPUT = "Permit approved. Expiration date: September 30, 2025."

# ------------------------------------------------------------------------------
# 🧪 Persona Preview Runner
# ------------------------------------------------------------------------------
def test_all_personas(raw_output: str, filter_avatar: str | None = None, output_json: bool = False):
    """
    Runs the same raw output through all defined personas (or a single one),
    and prints their tone, demeanor, style, and LLM-wrapped response.
    Optionally exports results to JSON.
    """
    llm = get_llm(temperature=0.7)
    results = []

    avatars = [filter_avatar] if filter_avatar else PERSONAS.keys()

    for avatar in avatars:
        traits = PERSONAS.get(avatar, PERSONAS["default"])
        system_prompt = build_flowbot_system_prompt(avatar)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{raw_output}")
        ])

        response = llm.invoke(prompt.format(raw_output=raw_output))

        result = {
            "avatar": avatar,
            "traits": traits,
            "response": response.content.strip()
        }

        results.append(result)

        # 📣 Print to console
        print(f"\n🌟 --- {avatar.upper()} ---")
        print(f"🗣️ Tone: {traits['tone']}")
        print(f"🎭 Demeanor: {traits['demeanor']}")
        print(f"📝 Style: {traits['style']}")
        print("💬 Response:")
        print(response.content.strip())

    # 📝 Optional JSON export
    if output_json:
        with open("persona_preview.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print("\n✅ Persona preview saved to persona_preview.json")

# ------------------------------------------------------------------------------
# 🚀 Entry Point
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FlowBot Persona Preview Harness")
    parser.add_argument("--avatar", help="Preview a single avatar")
    parser.add_argument("--json", action="store_true", help="Export results to persona_preview.json")
    args = parser.parse_args()

    test_all_personas(RAW_OUTPUT, filter_avatar=args.avatar, output_json=args.json)