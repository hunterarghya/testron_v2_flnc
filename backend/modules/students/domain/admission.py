"""The student admission state machine (domain_model.md §3.2, §7.1).

UNVERIFIED → PENDING → ACTIVE ⇄ DEACTIVATED; PENDING → DECLINED; ACTIVE/DEACTIVATED → ANONYMIZED.
"""

from collections.abc import Mapping, Sequence
from enum import StrEnum
from uuid import UUID

from core.context import StudentStatus
from modules.students.domain.bulk import BulkOutcome, plan, status_reason
from modules.students.domain.errors import AdmissionStepNotAllowed


class AdmissionAction(StrEnum):
    APPROVE = "APPROVE"
    DECLINE = "DECLINE"
    DEACTIVATE = "DEACTIVATE"
    REACTIVATE = "REACTIVATE"
    ANONYMIZE = "ANONYMIZE"


# action → (the statuses it starts from, the status it leads to)
_RULES: dict[AdmissionAction, tuple[frozenset[StudentStatus], StudentStatus]] = {
    AdmissionAction.APPROVE: (frozenset({StudentStatus.PENDING}), StudentStatus.ACTIVE),
    AdmissionAction.DECLINE: (frozenset({StudentStatus.PENDING}), StudentStatus.DECLINED),
    AdmissionAction.DEACTIVATE: (frozenset({StudentStatus.ACTIVE}), StudentStatus.DEACTIVATED),
    AdmissionAction.REACTIVATE: (frozenset({StudentStatus.DEACTIVATED}), StudentStatus.ACTIVE),
    AdmissionAction.ANONYMIZE: (
        frozenset({StudentStatus.ACTIVE, StudentStatus.DEACTIVATED}),
        StudentStatus.ANONYMIZED,
    ),
}


def can_apply(action: AdmissionAction, status: StudentStatus) -> bool:
    return status in _RULES[action][0]


def status_after(action: AdmissionAction) -> StudentStatus:
    return _RULES[action][1]


def plan_bulk(
    action: AdmissionAction,
    requested: Sequence[UUID],
    statuses: Mapping[UUID, StudentStatus],
) -> BulkOutcome:
    """A student already past this step (approved twice, say) is skipped, not an error."""
    return plan(
        requested,
        statuses,
        lambda _id, status: None if can_apply(action, status) else status_reason(status),
    )


def status_after_email_verified(status: StudentStatus) -> StudentStatus:
    """Verifying the email turns the account into a join request for the teacher."""
    if status is not StudentStatus.UNVERIFIED:
        raise AdmissionStepNotAllowed(context={"status": status})
    return StudentStatus.PENDING
