"""
config.py — Core configuration and defaults for PermitFlow-AI.

Responsibilities:
- Define application-wide constants and default settings.
- Centralize file paths for local JSON-based storage (to be replaced by Azure DB).
- Provide helper functions for loading configuration data.

Future Changes:
- When migrating to Azure DB, replace file path constants with DB connection settings.
- Keep DEFAULTS here so they remain the single source of truth.
"""

from pathlib import Path
import json

# ===== Base Paths =====
# BASE_DIR points to the /app directory so all paths are package-relative.
BASE_DIR = Path(__file__).resolve().parent.parent

# Directory containing local JSON "database" files.
# This can be moved or replaced without touching service code.
DB_DIR = BASE_DIR / "permitFlowDb"

# Specific file paths for current JSON storage
SITE_PROPERTIES_FILE = DB_DIR / "site_properties.json"
TOLLGATE_PROMPTS_FILE = DB_DIR / "tollgate_prompts.json"

# Path-safe reference to tollgates.yaml in the same folder as this file
# TOLLGATE_PROMPTS_FILE = Path(__file__).parent / "tollgates.yaml"

# ===== Default Site Properties =====
DEFAULTS = {
    "FLOWBOT_PREFERRED_NAME": "FlowBot",
    "SUPPORT_EMAIL": "support.permitflow@bettini.us",
    "DEFAULT_LANGUAGE": "en-US",
    "ALTERNATE_AVATARS": [
        {
            "avatar": "FlowBot",
            "demeanor": "Chippy",
            "icon": "/static/flowbot-avatar.png"
        }
    ]
}

# ===== Helper Functions =====
def load_site_properties():
    """
    Load site_properties.json from DB_DIR and merge with DEFAULTS.

    Returns:
        dict: Combined site properties with defaults applied.
    """
    if SITE_PROPERTIES_FILE.exists():
        with open(SITE_PROPERTIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**DEFAULTS, **data}
    return DEFAULTS