"""The student admission state machine (domain_model.md §7.1).

UNVERIFIED → PENDING → ACTIVE ⇄ DEACTIVATED; PENDING → DECLINED; ACTIVE/DEACTIVATED → ANONYMIZED.
"""

from core.context import StudentStatus
from modules.students.domain.errors import AdmissionStepNotAllowed


def status_after_email_verified(status: StudentStatus) -> StudentStatus:
    """Verifying the email turns the account into a join request for the teacher."""
    if status is not StudentStatus.UNVERIFIED:
        raise AdmissionStepNotAllowed(context={"status": status})
    return StudentStatus.PENDING
