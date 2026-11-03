"""Checks on what the teacher typed that more than one use case shares."""

from collections.abc import Sequence
from uuid import UUID

from modules.assignments.domain.audience import ensure_all_active, ensure_audience_not_empty
from modules.assignments.domain.settings import checked_password
from modules.assignments.services.password_cipher import encrypt_password
from modules.students import public as students


def active_audience(requested: Sequence[UUID]) -> list[UUID]:
    """At least one student, every one ACTIVE (domain_model.md §3.5 #1)."""
    ensure_audience_not_empty(requested)
    statuses = {s.student_id: s.status for s in students.describe_students(requested)}
    return ensure_all_active(requested, statuses)


def password_token(password: str | None, confirm: str | None) -> str | None:
    """The encrypted password, or None for no password (domain_model.md §3.5 #4)."""
    if password is None:
        return None
    return encrypt_password(checked_password(password, confirm))
