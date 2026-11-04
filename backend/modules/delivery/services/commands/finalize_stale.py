from datetime import datetime
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery.repositories import attempts, stage_progress, sweep
from modules.delivery.services.live import bring_up_to_date

BATCH = 200


def finalize_stale(ctx: Ctx, *, anchored_before: datetime | None, limit: int | None) -> int:
    """The safety net behind lazy finalization (database_schema.md §5.4): sittings nobody has
    looked at end at their deadline instant and are graded, as if a worker had done it.
    Housekeeping passes "started over 24 h ago" and a batch; `finalize_expired --all` passes
    neither. Sittings still within their time are left running. Returns how many ended. No
    policy: the callers are housekeeping and a management command."""
    ids = sweep.in_progress_ids(anchored_before=anchored_before, limit=limit)
    return sum(_end_expired(ctx, ids[start : start + BATCH]) for start in range(0, len(ids), BATCH))


def _end_expired(ctx: Ctx, ids: list[UUID]) -> int:
    """One transaction per batch; a sitting being written elsewhere is skipped, not waited for."""
    with transaction.atomic():
        running = attempts.lock_expirable(ids)
        stages = stage_progress.stages_by_attempt([a.id for a in running])
        live = [
            bring_up_to_date(
                ctx, a, assignments.get_sitting_terms(a.assignment_id, a.student_id), stages[a.id]
            )
            for a in running
        ]
    return sum(not item.attempt.in_progress for item in live)
