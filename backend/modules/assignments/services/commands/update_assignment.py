from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments.domain.assignment import SettingsPatch, checked_settings
from modules.assignments.domain.window import ensure_window_valid
from modules.assignments.repositories import assignments
from modules.assignments.services.changes import lock_for_change
from modules.assignments.services.views import AssignmentDetail, assignment_detail


def update_assignment(ctx: Ctx, *, assignment_id: UUID, patch: SettingsPatch) -> AssignmentDetail:
    """Change the overview's settings (T-08). Before the start everything but the test and
    paper; after it only the title and publication (domain_model.md §3.5 #5)."""
    with transaction.atomic():
        record = lock_for_change(ctx, assignment_id, patch.changed_fields())
        settings = checked_settings(patch.applied_to(record.settings))
        if patch.window is not None:
            ensure_window_valid(
                settings.window, now=ctx.now, total_duration_s=record.timeline.total_duration_s
            )
        assignments.update_settings(assignment_id, settings, now=ctx.now)
    return assignment_detail(assignments.get_record(assignment_id), now=ctx.now)
