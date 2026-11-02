"""A section's own fields: a short title and, for sectioned tests, its duration."""

from core.errors import FieldError, FieldsInvalid
from core.text import clean_text_line
from modules.authoring.domain.settings_patch import DURATION_SECONDS
from modules.authoring.domain.settings_rules import range_error

MAX_SECTION_TITLE_LENGTH = 120


def section_title(raw: str) -> str:
    title = clean_text_line(raw)
    if len(title) > MAX_SECTION_TITLE_LENGTH:
        message = f"Use at most {MAX_SECTION_TITLE_LENGTH} characters"
        raise FieldsInvalid(FieldError("title", "invalid", message))
    return title


def section_duration(seconds: int | None) -> int | None:
    """None is allowed in a draft; sectioned tests list it as a problem."""
    error = None if seconds is None else range_error("duration_s", seconds, DURATION_SECONDS)
    if error:
        raise FieldsInvalid(error)
    return seconds
