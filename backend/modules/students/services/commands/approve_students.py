from collections.abc import Sequence
from uuid import UUID

from core.context import Ctx
from modules.students.domain.admission import AdmissionAction, BulkOutcome
from modules.students.services.admission_changes import change_admission


def approve_students(ctx: Ctx, *, student_ids: Sequence[UUID]) -> BulkOutcome:
    """Approve join requests: PENDING students become ACTIVE and can use the portal
    (domain_model.md §3.2, T-14 Pending). Group selection on approval arrives with groups
    (step 2.1). Students not in the right status are skipped, not refused.
    """
    return change_admission(ctx, AdmissionAction.APPROVE, student_ids)
