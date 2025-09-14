# app/core/config_loader.py
from __future__ import annotations
from pathlib import Path
from typing import Any
import json

# ===== Base Paths =====
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "permitFlowDb"

GENERAL_INTENTS_PATH = DB_DIR / "general_intents.json"
SITE_PROPERTIES_FILE = DB_DIR / "site_properties.json"
PERSONAS_FILE = DB_DIR / "personas.json"
AVATARS_FILE = DB_DIR / "avatars.json"

# ===== Generic Loader =====
def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ===== Specific Loaders =====
def load_general_intents() -> dict[str, Any]:
    return load_json(GENERAL_INTENTS_PATH)

def load_personas() -> dict[str, Any]:
    return load_json(PERSONAS_FILE)

def load_avatars() -> dict[str, Any]:
    return load_json(AVATARS_FILE)

# ===== Preload configs =====
GENERAL_INTENTS = load_general_intents()
PERSONAS = load_personas()
AVATAR_MAP = load_avatars()

# ===== Avatar Helpers =====
def get_alternate_avatars(exclude: str | None = None) -> list[dict[str, Any]]:
    alternates: list[dict[str, Any]] = []
    for avatar_name, data in AVATAR_MAP.items():
        if exclude and avatar_name == exclude:
            continue
        persona_key = data.get("persona", "default")
        demeanor = PERSONAS.get(persona_key, {}).get("demeanor", "")
        alternates.append({
            "avatar": avatar_name,
            "persona": persona_key,
            "demeanor": demeanor.title(),
            "icon": data.get("icon"),
            "default": data.get("default", False)
        })
    return alternates

# ===== Defaults =====
DEFAULTS: dict[str, Any] = {
    "FLOWBOT_PREFERRED_NAME": "FlowBot",
    "SUPPORT_EMAIL": "support.permitflow@bettini.us",
    "DEFAULT_LANGUAGE": "en-US",
    "ALTERNATE_AVATARS": get_alternate_avatars()
}

# ===== Site Properties Loader =====
def load_site_properties() -> dict[str, Any]:
    props = DEFAULTS.copy()
    if SITE_PROPERTIES_FILE.exists():
        file_data = load_json(SITE_PROPERTIES_FILE)
        props.update(file_data)
    props["ALTERNATE_AVATARS"] = get_alternate_avatars()
    return props

SITE_PROPERTIES = load_site_properties()