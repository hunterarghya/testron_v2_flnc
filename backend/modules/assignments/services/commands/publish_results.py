from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments.domain.publishing import PublicationChanges, publish
from modules.assignments.repositories import assignments
from modules.assignments.services.changes import lock_started
from modules.assignments.services.views import AssignmentDetail, assignment_detail


def publish_results(
    ctx: Ctx, *, assignment_id: UUID, changes: PublicationChanges
) -> AssignmentDetail:
    """D-01 Publish (domain_model.md §6.4): every graded result becomes visible now, with the
    options chosen in the dialog; any automatic mode gives way to this."""
    with transaction.atomic():
        record = lock_started(ctx, assignment_id)
        done = publish(record.settings.publication, changes, now=ctx.now)
        assignments.set_publication(
            assignment_id, done.publication, published_at=done.published_at, now=ctx.now
        )
    return assignment_detail(assignments.get_record(assignment_id), now=ctx.now)
