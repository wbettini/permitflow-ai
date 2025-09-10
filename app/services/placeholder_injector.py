"""
placeholder_injector.py — Dynamic placeholder replacement service.

Responsibilities:
- Replace placeholders in template strings with runtime values.
- Keep placeholder logic centralized for maintainability.

Supported Placeholders:
- {user_name}
- {time_of_day}
- {last_topic}

Future Changes:
- Add conditional placeholders (e.g., {if_user_name}).
- Support nested or computed placeholders.
"""

from typing import Dict
from app.core.logger import logger


# ===== Public API =====
def inject_placeholders(template: str, values: Dict[str, str]) -> str:
    """
    Replace placeholders in the template with provided values.

    Args:
        template (str): The template string containing placeholders.
        values (dict): Mapping of placeholder names to replacement values.

    Returns:
        str: Template with placeholders replaced.
    """
    result = template
    for key, val in values.items():
        result = result.replace(f"{{{key}}}", str(val))
    logger.debug(f"[Placeholders Injected] values={values}, result={result}")
    return result