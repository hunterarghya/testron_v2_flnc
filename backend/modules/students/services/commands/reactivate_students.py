from collections.abc import Sequence
from uuid import UUID

from core.context import Ctx
from modules.students.domain.admission import AdmissionAction, BulkOutcome
from modules.students.services.admission_changes import change_admission


def reactivate_students(ctx: Ctx, *, student_ids: Sequence[UUID]) -> BulkOutcome:
    """Reactivate students: DEACTIVATED students become ACTIVE again, with their history untouched
    (domain_model.md §7.1). Students not in the right status are skipped, not refused.
    """
    return change_admission(ctx, AdmissionAction.REACTIVATE, student_ids)
