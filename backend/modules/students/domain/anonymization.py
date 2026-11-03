"""Deleting a student keeps their results but removes who they were (domain_model.md §3.2 #3)."""

from core.errors import ConfirmationMismatch
from core.text import clean_text_line

# `.invalid` is reserved and never routable: mail can't reach a deleted student
_PLACEHOLDER_DOMAIN = "anonymized.invalid"


def anonymized_name(number: int) -> str:
    return f"Deleted student #{number}"


def anonymized_email(number: int) -> str:
    return f"deleted-student-{number}@{_PLACEHOLDER_DOMAIN}"


def ensure_name_confirmed(typed: str, *, name: str) -> None:
    """The teacher must type the student's name exactly (security.md T-08)."""
    if clean_text_line(typed) != name:
        raise ConfirmationMismatch()
