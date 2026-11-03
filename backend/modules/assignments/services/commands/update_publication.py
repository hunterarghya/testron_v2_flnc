from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments.domain.publishing import PublicationChanges, edit
from modules.assignments.repositories import assignments
from modules.assignments.services.changes import lock_for_change
from modules.assignments.services.views import AssignmentDetail, assignment_detail


def update_publication(
    ctx: Ctx, *, assignment_id: UUID, changes: PublicationChanges
) -> AssignmentDetail:
    """T-08/T-11: change how and what results show, any time (domain_model.md §3.5 #5). A new
    mode starts afresh, so results published by hand are hidden until it says otherwise."""
    with transaction.atomic():
        record = lock_for_change(ctx, assignment_id, ["publication"])
        done = edit(record.settings.publication, record.published_at, changes)
        assignments.set_publication(
            assignment_id, done.publication, published_at=done.published_at, now=ctx.now
        )
    return assignment_detail(assignments.get_record(assignment_id), now=ctx.now)
