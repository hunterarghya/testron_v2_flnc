import pytest

from conftest import MakeCtx
from core.errors import RateLimited
from modules.identity.domain.errors import EmailNotVerified, InvalidCredentials
from modules.identity.services.commands.authenticate_password import authenticate_password
from tests.factories.identity import make_user

pytestmark = pytest.mark.django_db
PASSWORD = "correct-horse-battery"


def log_in(make_ctx: MakeCtx, email: str = "rina@example.com", password: str = PASSWORD) -> object:
    return authenticate_password(make_ctx(), email=email, password=password, client_ip="ip")


def test_right_password_opens_the_account(make_ctx: MakeCtx) -> None:
    user = make_user(email="rina@example.com")

    assert log_in(make_ctx) == user.id


@pytest.mark.parametrize(
    ("email", "password"),
    [("rina@example.com", "wrong-password"), ("nobody@example.com", PASSWORD)],
    ids=["wrong-password", "unknown-email"],
)
def test_every_failure_is_the_same_error(make_ctx: MakeCtx, email: str, password: str) -> None:
    make_user(email="rina@example.com")

    with pytest.raises(InvalidCredentials):
        log_in(make_ctx, email, password)


def test_google_only_account_has_no_password_to_match(make_ctx: MakeCtx) -> None:
    make_user(email="rina@example.com", google_only=True)

    with pytest.raises(InvalidCredentials):
        log_in(make_ctx)


def test_unverified_email_is_reported_only_after_the_password_matched(make_ctx: MakeCtx) -> None:
    make_user(email="rina@example.com", email_verified_at=None)

    with pytest.raises(InvalidCredentials):
        log_in(make_ctx, password="wrong-password")
    with pytest.raises(EmailNotVerified) as error:
        log_in(make_ctx)

    assert error.value.context == {"email_masked": "r•••@example.com"}


def test_inactive_but_verified_accounts_can_log_in(make_ctx: MakeCtx) -> None:
    # Pending, declined and deactivated students see their status screen
    user = make_user(email="rina@example.com", is_active=False)

    assert log_in(make_ctx) == user.id


def test_ten_tries_per_email_then_a_pause(make_ctx: MakeCtx) -> None:
    make_user(email="rina@example.com")
    for _ in range(10):
        with pytest.raises(InvalidCredentials):
            log_in(make_ctx, password="wrong-password")

    with pytest.raises(RateLimited):
        log_in(make_ctx)
