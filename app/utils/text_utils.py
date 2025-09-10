"""
text_utils.py — Text normalization, synonym expansion, and typo correction utilities.
"""

import re
from typing import Dict, List, Set

# =============================================================================
# Synonym & Typo Maps
# =============================================================================

SYNONYM_MAP: Dict[str, List[str]] = {
    "what time is it": ["current time", "tell me the hour", "time now", "clock"],
    "what is the date": ["today's date", "current date", "day today"],
    "permit": ["license", "approval", "authorization"],
    "tollgate": ["toll gate", "checkpoint", "milestone"],
}

COMMON_TYPO_MAP: Dict[str, str] = {
    "teh": "the",
    "yeh": "the",
    "whats": "what's",
    "todays": "today's",
    "calender": "calendar"
}

# =============================================================================
# Text Processing Functions
# =============================================================================

def correct_typos(text: str) -> str:
    """Correct common typos before normalization."""
    words = text.split()
    corrected = [COMMON_TYPO_MAP.get(w.lower(), w) for w in words]
    return " ".join(corrected)

def normalize_text(text: str) -> str:
    """Correct typos, lowercase, strip punctuation, and collapse whitespace."""
    corrected = correct_typos(text)
    cleaned = re.sub(r"[^\w\s]", "", corrected)
    return re.sub(r"\s+", " ", cleaned).strip().lower()

def expand_with_synonyms(text: str) -> Set[str]:
    """
    Return normalized text plus any known synonyms.

    Args:
        text: Raw input string.

    Returns:
        Set of normalized variants including synonyms.
    """
    norm = normalize_text(text)
    expanded = {norm}
    for base, synonyms in SYNONYM_MAP.items():
        if norm == base or norm in synonyms:
            expanded.add(base)
            expanded.update(synonyms)
    return expanded
