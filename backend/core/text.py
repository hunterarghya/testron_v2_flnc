"""Cleaning short user-typed text such as names (security.md §4.3)."""

import unicodedata

# Names of people and groups (database_schema.md §0)
MAX_NAME_LENGTH = 120

# Zero-width non-joiner and joiner shape Bengali conjuncts, so they must survive
_SHAPING_CHARACTERS = frozenset({chr(0x200C), chr(0x200D)})
# Control, invisible-format (incl. bidi overrides that can spoof text), private-use, surrogate
_REMOVED_CATEGORIES = frozenset({"Cc", "Cf", "Co", "Cs"})


def clean_text_line(raw: str) -> str:
    """One tidy line: Unicode-normalized, hidden characters removed, spaces collapsed."""
    text = unicodedata.normalize("NFC", raw)
    kept = "".join(character for character in text if _is_kept(character))
    return " ".join(kept.split())


def _is_kept(character: str) -> bool:
    if character.isspace() or character in _SHAPING_CHARACTERS:
        return True
    return unicodedata.category(character) not in _REMOVED_CATEGORIES
