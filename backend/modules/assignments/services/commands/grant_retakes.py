from collections.abc import Sequence
from uuid import UUID

from django.db import transaction

from core.bulk import BulkOutcome
from core.context import Ctx
from modules.assignments.domain.live_controls import plan_grants
from modules.assignments.repositories import audience, retake_grants
from modules.assignments.services.changes import lock_started


def grant_retakes(ctx: Ctx, *, assignment_id: UUID, student_ids: Sequence[UUID]) -> BulkOutcome:
    """D-02 Unlock retake (domain_model.md §5.7, D-9): one more sitting each, on its own clock,
    any time after the start, even after the test closed. A student who missed it gets a
    late first sitting (DM-6). Students outside the audience are skipped."""
    with transaction.atomic():
        lock_started(ctx, assignment_id)
        outcome = plan_grants(student_ids, set(audience.member_ids(assignment_id)))
        retake_grants.insert_grants(assignment_id, outcome.applied, now=ctx.now)
    return outcome
