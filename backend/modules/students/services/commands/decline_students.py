from collections.abc import Sequence
from uuid import UUID

from core.context import Ctx
from modules.students.domain.admission import AdmissionAction, BulkOutcome
from modules.students.services.admission_changes import change_admission


def decline_students(ctx: Ctx, *, student_ids: Sequence[UUID]) -> BulkOutcome:
    """Decline join requests: PENDING students become DECLINED. It is final: the account can't ask
    again (domain_model.md §3.2 #1, V1 F-30). They stay logged in, so they can read "Request
    declined". Students not in the right status are skipped, not refused.
    """
    return change_admission(ctx, AdmissionAction.DECLINE, student_ids)
