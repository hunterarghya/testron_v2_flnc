import pytest

from conftest import AfterCommit, MakeCtx, last_emailed_code
from core.clock import FrozenClock
from core.context import Role, StudentStatus
from core.errors import RateLimited
from modules.identity.public import OtpInvalid, find_user_id_by_email, get_user_summary
from modules.students.models import Student
from modules.students.services.commands.sign_up_with_password import sign_up_with_password
from modules.students.services.commands.verify_email import verify_email
from modules.students.services.session_user import SessionUserView

pytestmark = pytest.mark.django_db
EMAIL = "rina@example.com"


@pytest.fixture
def code(make_ctx: MakeCtx, after_commit: AfterCommit) -> str:
    """A fresh sign-up's emailed code."""
    with after_commit():
        sign_up_with_password(
            make_ctx(), name="Rina Das", email=EMAIL, password="a-long-passphrase", client_ip="ip"
        )
    return last_emailed_code()


def verify(make_ctx: MakeCtx, code: str, *, email: str = EMAIL) -> SessionUserView:
    return verify_email(make_ctx(), email=email, code=code, client_ip="10.0.0.1")


def test_right_code_turns_the_account_into_a_join_request(
    make_ctx: MakeCtx, frozen_clock: FrozenClock, code: str
) -> None:
    view = verify(make_ctx, code)

    user_id = find_user_id_by_email(EMAIL)
    assert user_id is not None
    student = Student.objects.get(user_id=user_id)
    assert student.status == StudentStatus.PENDING
    assert student.requested_at == frozen_clock.now()
    assert get_user_summary(user_id).email_verified
    assert (view.role, view.status, view.has_password) == (
        Role.STUDENT,
        StudentStatus.PENDING,
        True,
    )


def test_wrong_code_changes_nothing(make_ctx: MakeCtx, code: str) -> None:
    wrong = "111111" if code != "111111" else "222222"

    with pytest.raises(OtpInvalid):
        verify(make_ctx, wrong)

    assert Student.objects.get().status == StudentStatus.UNVERIFIED


def test_unknown_email_gets_the_same_answer(make_ctx: MakeCtx, code: str) -> None:
    with pytest.raises(OtpInvalid):
        verify(make_ctx, code, email="nobody@example.com")


def test_v1_f01_missing_code_is_rejected(make_ctx: MakeCtx, code: str) -> None:
    with pytest.raises(OtpInvalid):
        verify(make_ctx, "")

    assert Student.objects.get().status == StudentStatus.UNVERIFIED


def test_a_code_works_once(make_ctx: MakeCtx, code: str) -> None:
    verify(make_ctx, code)

    with pytest.raises(OtpInvalid):
        verify(make_ctx, code)


def test_guessing_across_accounts_from_one_address_is_limited(make_ctx: MakeCtx) -> None:
    for _ in range(30):
        with pytest.raises(OtpInvalid):
            verify(make_ctx, "123456", email="nobody@example.com")

    with pytest.raises(RateLimited):
        verify(make_ctx, "123456", email="nobody@example.com")
