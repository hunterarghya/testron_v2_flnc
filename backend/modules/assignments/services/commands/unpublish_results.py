from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments.domain.publishing import unpublish
from modules.assignments.repositories import assignments
from modules.assignments.services.changes import lock_started
from modules.assignments.services.views import AssignmentDetail, assignment_detail


def unpublish_results(ctx: Ctx, *, assignment_id: UUID) -> AssignmentDetail:
    """T-11 Unpublish (E-28): every result is hidden again ("Awaiting results"), and stays so
    until the teacher publishes; automatic publishing is switched off."""
    with transaction.atomic():
        record = lock_started(ctx, assignment_id)
        done = unpublish(record.settings.publication)
        assignments.set_publication(
            assignment_id, done.publication, published_at=done.published_at, now=ctx.now
        )
    return assignment_detail(assignments.get_record(assignment_id), now=ctx.now)
