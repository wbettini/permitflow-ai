"""
site_properties_service.py — Service for retrieving site properties.

Responsibilities:
- Load site properties from JSON file (local dev) or future DB source.
- Merge loaded values with application defaults from config.py.

Future Changes:
- Replace JSON file read with Azure DB query.
- Keep DEFAULTS in config.py as the single source of truth.
"""

from app.core.config import load_site_properties

# ===== Public API =====
def get_site_properties():
    """
    Retrieve site properties merged with defaults.

    Returns:
        dict: Site properties dictionary.
    """
    return load_site_properties()