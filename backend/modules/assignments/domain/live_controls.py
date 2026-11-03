"""The teacher's controls while a test runs (T-10; domain_model.md §3.5, §5.2, §5.7): extra
time, retakes and "end for everyone". Each needs the test to have started."""

from collections.abc import Collection, Sequence
from uuid import UUID

from core.bulk import NOT_FOUND, BulkOutcome, Skip
from core.errors import Conflict, FieldError, FieldsInvalid

# The same bound as the database's (extensions_seconds_range): up to a day at a time
MAX_EXTENSION_S = 86_400


class AssignmentNotStarted(Conflict):
    """Extra time, retakes and ending mean nothing before anyone could sit the test."""

    code = "assignment_not_started"
    title = "This test hasn't started yet"


def ensure_started(started: bool) -> None:
    if not started:
        raise AssignmentNotStarted()


def ensure_extension_valid(
    seconds: int, stage_index: int | None, *, stage_count: int, unknown_students: Collection[UUID]
) -> None:
    """Every problem at once: the length, the stage (None = the final one), the students."""
    errors = []
    if not 1 <= seconds <= MAX_EXTENSION_S:
        errors.append(FieldError("seconds", "invalid", "Use up to 24 hours"))
    if stage_index is not None and not 0 <= stage_index < stage_count:
        errors.append(FieldError("stage_index", "invalid", "Pick a section of this test"))
    if unknown_students:
        errors.append(FieldError("student_ids", "invalid", "Pick students who sit this test"))
    if errors:
        raise FieldsInvalid(*errors)


def plan_grants(requested: Sequence[UUID], members: Collection[UUID]) -> BulkOutcome:
    """One more sitting each, for students in the audience only (once each, however often
    they are listed)."""
    wanted = list(dict.fromkeys(requested))
    return BulkOutcome(
        applied=tuple(s for s in wanted if s in members),
        skipped=tuple(Skip(s, NOT_FOUND) for s in wanted if s not in members),
    )
