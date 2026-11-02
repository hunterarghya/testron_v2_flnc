"""The student admission state machine (domain_model.md §3.2, §7.1).

UNVERIFIED → PENDING → ACTIVE ⇄ DEACTIVATED; PENDING → DECLINED; ACTIVE/DEACTIVATED → ANONYMIZED.
Teacher actions are bulk: each student is changed or skipped on their own (§3.2 #4).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from core.context import StudentStatus
from modules.students.domain.errors import AdmissionStepNotAllowed

NOT_FOUND = "not_found"


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


@dataclass(frozen=True, slots=True)
class Skip:
    student_id: UUID
    # "not_found", or the status that made the action not apply, e.g. "status_active"
    reason: str


@dataclass(frozen=True, slots=True)
class BulkOutcome:
    applied: tuple[UUID, ...]
    skipped: tuple[Skip, ...]


def can_apply(action: AdmissionAction, status: StudentStatus) -> bool:
    return status in _RULES[action][0]


def status_after(action: AdmissionAction) -> StudentStatus:
    return _RULES[action][1]


def plan_bulk(
    action: AdmissionAction,
    requested: Sequence[UUID],
    statuses: Mapping[UUID, StudentStatus],
) -> BulkOutcome:
    """Which requested students the action applies to, and why the rest are skipped.

    A student already past this step (approved twice, say) is skipped, not an error.
    Each id counts once, in the order given.
    """
    apply: list[UUID] = []
    skipped: list[Skip] = []
    for student_id in dict.fromkeys(requested):
        status = statuses.get(student_id)
        if status is None:
            skipped.append(Skip(student_id, NOT_FOUND))
        elif can_apply(action, status):
            apply.append(student_id)
        else:
            skipped.append(Skip(student_id, f"status_{status.value.lower()}"))
    return BulkOutcome(applied=tuple(apply), skipped=tuple(skipped))


def status_after_email_verified(status: StudentStatus) -> StudentStatus:
    """Verifying the email turns the account into a join request for the teacher."""
    if status is not StudentStatus.UNVERIFIED:
        raise AdmissionStepNotAllowed(context={"status": status})
    return StudentStatus.PENDING
