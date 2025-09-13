from pathlib import Path
import json
from app.prompts.flowbot_prompts import AVATAR_MAP, PERSONAS

# ===== Base Paths =====
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "permitFlowDb"

GENERAL_INTENTS_PATH = DB_DIR / "general_intents.json"
SITE_PROPERTIES_FILE = DB_DIR / "site_properties.json"

# ===== Loaders =====
def load_general_intents():
    with open(GENERAL_INTENTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

GENERAL_INTENTS = load_general_intents()

# ===== Avatar Helpers =====
def get_alternate_avatars(exclude: str | None = None) -> list[dict]:
    """
    Build a list of alternate avatars from avatars.json and personas.json.
    """
    alternates = []
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

# ===== Default Site Properties =====
DEFAULTS = {
    "FLOWBOT_PREFERRED_NAME": "FlowBot",
    "SUPPORT_EMAIL": "support.permitflow@bettini.us",
    "DEFAULT_LANGUAGE": "en-US",
    "ALTERNATE_AVATARS": get_alternate_avatars()
}

# ===== Site Properties Loader =====
def load_site_properties():
    """
    Load site_properties.json from DB_DIR and merge with DEFAULTS.
    Always regenerates ALTERNATE_AVATARS from avatars.json.
    """
    props = DEFAULTS.copy()

    if SITE_PROPERTIES_FILE.exists():
        with open(SITE_PROPERTIES_FILE, "r", encoding="utf-8") as f:
            file_data = json.load(f)
        props.update(file_data)

    # Always overwrite with live avatar list
    props["ALTERNATE_AVATARS"] = get_alternate_avatars()
    return props