import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "permitFlowDb"

def load_config(filename: str) -> dict:
    with open(DB_PATH / filename, "r", encoding="utf-8") as f:
        return json.load(f)

PERSONAS = load_config("personas.json")
AVATAR_MAP = load_config("avatars.json")