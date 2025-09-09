"""
tollgate_service.py — Service for retrieving tollgate prompts.

Responsibilities:
- Load tollgate prompts from JSON file (local dev) or future DB source.
- Provide a clean interface for routers to access prompt data.

Future Changes:
- Replace JSON file read with Azure DB query.
- Keep file path centralized in config.py for easy migration.
"""

import json
from app.core.config import TOLLGATE_PROMPTS_FILE

# ===== Public API =====
def get_tollgate_prompts():
    """
    Retrieve tollgate prompts from the configured JSON file.

    Returns:
        dict: Tollgate prompts data or error message if file not found.
    """
    if TOLLGATE_PROMPTS_FILE.exists():
        with open(TOLLGATE_PROMPTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"error": f"{TOLLGATE_PROMPTS_FILE.name} not found"}