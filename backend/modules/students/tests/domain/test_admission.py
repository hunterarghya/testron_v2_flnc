import pytest

from core.context import StudentStatus
from modules.students.domain.admission import status_after_email_verified
from modules.students.domain.errors import AdmissionStepNotAllowed


def test_verified_email_makes_a_join_request() -> None:
    assert status_after_email_verified(StudentStatus.UNVERIFIED) is StudentStatus.PENDING


@pytest.mark.parametrize(
    "status", [status for status in StudentStatus if status is not StudentStatus.UNVERIFIED]
)
def test_only_unverified_accounts_can_be_verified(status: StudentStatus) -> None:
    with pytest.raises(AdmissionStepNotAllowed):
        status_after_email_verified(status)
