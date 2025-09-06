# core/site_properties.py
import json
from pathlib import Path

SITE_PROPERTIES_PATH = Path(__file__).parent.parent / "permitFlowDb" / "site_properties.json"

# Optional: cache the properties so we don't re-read the file every time
_site_properties_cache = None

def get_site_property(key: str, default=None):
    global _site_properties_cache
    if _site_properties_cache is None:
        with open(SITE_PROPERTIES_PATH, "r", encoding="utf-8") as f:
            _site_properties_cache = json.load(f)
    return _site_properties_cache.get(key, default)