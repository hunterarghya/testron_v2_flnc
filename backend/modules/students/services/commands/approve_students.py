from collections.abc import Sequence
from uuid import UUID

from django.db import transaction

from core.bulk import BulkOutcome
from core.context import Ctx
from modules.students.domain.admission import AdmissionAction
from modules.students.repositories import memberships
from modules.students.services.admission_changes import change_admission
from modules.students.services.group_access import lock_active_group


def approve_students(
    ctx: Ctx, *, student_ids: Sequence[UUID], group_ids: Sequence[UUID] = ()
) -> BulkOutcome:
    """Approve join requests: PENDING students become ACTIVE and can use the portal, and join
    the chosen groups at the same time (domain_model.md §3.2, T-14 Pending). Students not in
    the right status are skipped, not refused; an archived or unknown group refuses it all.
    """
    with transaction.atomic():
        for group_id in dict.fromkeys(group_ids):
            lock_active_group(group_id)
        outcome = change_admission(ctx, AdmissionAction.APPROVE, student_ids)
        for group_id in dict.fromkeys(group_ids):
            memberships.add_members(group_id, outcome.applied, now=ctx.now)
    return outcome
