# routers/persona_preview.py

from fastapi import APIRouter, Query
from app.prompts.flowbot_prompts import build_flowbot_system_prompt
from app.langchain_config import get_llm
from pathlib import Path
import json

router = APIRouter()

# Load persona traits for metadata
DB_PATH = Path(__file__).parent.parent / "permitFlowDb"
with open(DB_PATH / "personas.json", "r", encoding="utf-8") as f:
    PERSONAS = json.load(f)

@router.get("/persona-preview")
def preview_persona(avatar: str = Query(...), raw_output: str = Query(...)):
    """
    Returns a preview of how the selected FlowBot avatar would respond to a given output.
    Useful for UI testing, tone validation, and contributor feedback.
    """
    system_prompt = build_flowbot_system_prompt(avatar)
    llm = get_llm()
    response = llm.invoke(system_prompt + "\n\n" + raw_output)

    return {
        "avatar": avatar,
        "traits": PERSONAS.get(avatar, {}),
        "response": response.content.strip()
    }