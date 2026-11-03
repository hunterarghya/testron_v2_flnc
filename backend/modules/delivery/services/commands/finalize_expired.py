from collections.abc import Sequence
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery.domain.gate import Sittings
from modules.delivery.repositories import attempt_facts, attempts, stage_progress
from modules.delivery.services.live import bring_up_to_date


def finalize_expired(
    ctx: Ctx, student_id: UUID, mine: Sequence[assignments.StudentAssignment]
) -> dict[UUID, Sittings]:
    """Lazy finalization before a student's list or gate is read (database_schema.md §5.2):
    their sittings whose time ran out end at the deadline instant and are graded, even if the
    browser was closed long ago (E-03). Returns their sittings as they are after that. Nothing
    is locked unless a sitting is in progress. No policy: callers are delivery's use cases,
    after their own."""
    ids = [assignment.assignment_id for assignment in mine]
    sittings = attempt_facts.sittings_by_assignment(student_id, ids)
    running = [s.in_progress_attempt_id for s in sittings.values() if s.in_progress_attempt_id]
    if running and _end_expired(ctx, running, mine):
        sittings = attempt_facts.sittings_by_assignment(student_id, ids)
    return sittings


def _end_expired(
    ctx: Ctx, attempt_ids: list[UUID], mine: Sequence[assignments.StudentAssignment]
) -> bool:
    """True if any ended. One the hall is ending right now is skipped, not waited for."""
    terms = {assignment.assignment_id: assignment for assignment in mine}
    with transaction.atomic():
        running = attempts.lock_expirable(attempt_ids)
        stages = stage_progress.stages_by_attempt([attempt.id for attempt in running])
        live = [
            bring_up_to_date(ctx, attempt, terms[attempt.assignment_id], stages[attempt.id])
            for attempt in running
        ]
    return any(not item.attempt.in_progress for item in live)
