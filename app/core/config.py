# app/core/config.py --- Central constants for PermitFlow AI

from app.core.config_loader import (
    SITE_PROPERTIES,   # merged defaults + file values, preloaded
    GENERAL_INTENTS,   # from general_intents.json
    PERSONAS,          # from personas.json
    AVATAR_MAP         # from avatars.json
)

# Example: expose a global constant from site properties
MAX_CONTEXT_TURNS = SITE_PROPERTIES.get("MAX_CONTEXT_TURNS", 5)