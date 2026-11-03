"""Who sits an assignment: the explicit list the teacher confirmed (domain_model.md §3.5 #3,
[D-1]). Groups only help pick; later group changes never touch it."""

from collections.abc import Collection, Mapping, Sequence
from uuid import UUID

from core.bulk import NOT_FOUND, BulkOutcome, Skip
from core.context import StudentStatus
from core.errors import FieldError, FieldsInvalid
from modules.assignments.domain.errors import AudienceMemberHasAttempt

ALREADY_MEMBER = "already_member"
NOT_MEMBER = "not_member"


def ensure_audience_not_empty(student_ids: Collection[UUID]) -> None:
    if not student_ids:
        raise FieldsInvalid(FieldError("student_ids", "required", "Pick at least one student"))


def ensure_all_active(
    requested: Sequence[UUID], statuses: Mapping[UUID, StudentStatus]
) -> list[UUID]:
    """A new audience takes ACTIVE students only; anyone else is a field error."""
    unknown = [sid for sid in requested if statuses.get(sid) is not StudentStatus.ACTIVE]
    if unknown:
        raise FieldsInvalid(
            FieldError("student_ids", "invalid", f"{len(unknown)} of these can't take tests")
        )
    return list(dict.fromkeys(requested))


def plan_additions(
    requested: Sequence[UUID], statuses: Mapping[UUID, StudentStatus], members: Collection[UUID]
) -> BulkOutcome:
    """ACTIVE students who aren't in yet are added; everyone else is skipped with a reason."""
    applied: list[UUID] = []
    skipped: list[Skip] = []
    for sid in dict.fromkeys(requested):
        reason = _addition_skip(sid, statuses.get(sid), members)
        if reason is None:
            applied.append(sid)
        else:
            skipped.append(Skip(sid, reason))
    return BulkOutcome(tuple(applied), tuple(skipped))


def plan_removals(
    requested: Sequence[UUID], members: Collection[UUID], with_attempt: Collection[UUID]
) -> BulkOutcome:
    """Members leave unless they have started (E-11): then nothing is removed at all."""
    started = [sid for sid in requested if sid in with_attempt]
    if started:
        raise AudienceMemberHasAttempt(started)
    unique = list(dict.fromkeys(requested))
    return BulkOutcome(
        tuple(sid for sid in unique if sid in members),
        tuple(Skip(sid, NOT_MEMBER) for sid in unique if sid not in members),
    )


def _addition_skip(
    sid: UUID, status: StudentStatus | None, members: Collection[UUID]
) -> str | None:
    if status is None:
        return NOT_FOUND
    if status is not StudentStatus.ACTIVE:
        return f"status_{status.value.lower()}"
    return ALREADY_MEMBER if sid in members else None
