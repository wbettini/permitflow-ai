from app.core.config_loader import load_site_properties

def get_site_properties() -> dict:
    """Return the latest site properties (merged with defaults)."""
    return load_site_properties()