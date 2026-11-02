"""Bulk actions on students: each requested student is applied or skipped with a reason, never
refused as a whole (domain_model.md §3.2 #4). Admission, group membership and performance
sharing all plan their changes here."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from uuid import UUID

from core.context import StudentStatus

NOT_FOUND = "not_found"
# Students who were admitted: the only ones who can be in groups or see their performance
ADMITTED = frozenset({StudentStatus.ACTIVE, StudentStatus.DEACTIVATED})


@dataclass(frozen=True, slots=True)
class Skip:
    student_id: UUID
    # "not_found", "status_<status>", or what made the change pointless ("already_member", …)
    reason: str


@dataclass(frozen=True, slots=True)
class BulkOutcome:
    applied: tuple[UUID, ...]
    skipped: tuple[Skip, ...]


# (student id, status) → why it is skipped, or None to apply it
SkipReason = Callable[[UUID, StudentStatus], str | None]


def plan(
    requested: Sequence[UUID], statuses: Mapping[UUID, StudentStatus], skip_reason: SkipReason
) -> BulkOutcome:
    """Each id counts once, in the order given; ids that aren't students are not_found."""
    applied: list[UUID] = []
    skipped: list[Skip] = []
    for student_id in dict.fromkeys(requested):
        status = statuses.get(student_id)
        reason = NOT_FOUND if status is None else skip_reason(student_id, status)
        if reason is None:
            applied.append(student_id)
        else:
            skipped.append(Skip(student_id, reason))
    return BulkOutcome(applied=tuple(applied), skipped=tuple(skipped))


def status_reason(status: StudentStatus) -> str:
    return f"status_{status.value.lower()}"


def unless_admitted(status: StudentStatus) -> str | None:
    """Skip reason for a student who was never admitted (or was deleted)."""
    return None if status in ADMITTED else status_reason(status)
