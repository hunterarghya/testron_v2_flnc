"""Tag names: one canonical form per tag, the display form as first typed (domain_model.md §4.1)."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from core.errors import FieldError, FieldsInvalid
from core.text import clean_text_line

MAX_TAG_NAME_LENGTH = 80


class TagKind(StrEnum):
    CHAPTER = "CHAPTER"
    TOPIC = "TOPIC"


@dataclass(frozen=True, slots=True)
class TagRef:
    id: UUID
    kind: TagKind
    name: str


def display_tag_name(raw: str) -> str:
    """The tag as shown: trimmed, spaces collapsed, hidden characters removed. 1 to 80 chars."""
    name = clean_text_line(raw)
    if not name or len(name) > MAX_TAG_NAME_LENGTH:
        raise FieldsInvalid(
            FieldError("name", "invalid", f"Use 1 to {MAX_TAG_NAME_LENGTH} characters")
        )
    return name


def normalize_tag_name(raw: str) -> str:
    """'Cell', 'cell ' and 'CELL' are one tag. casefold() is Unicode-aware, so Bengali works."""
    return clean_text_line(raw).casefold()
