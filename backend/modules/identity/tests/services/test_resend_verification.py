import pytest
from django.core import mail

from conftest import AfterCommit, MakeCtx
from core.clock import FrozenClock
from core.errors import RateLimited
from modules.identity.models import EmailOtp
from modules.identity.services.commands.resend_verification import resend_verification
from tests.factories.identity import make_user

pytestmark = pytest.mark.django_db


def resend(make_ctx: MakeCtx, after_commit: AfterCommit, email: str) -> None:
    with after_commit():
        resend_verification(make_ctx(), email=email)


def test_unverified_account_gets_a_new_code(make_ctx: MakeCtx, after_commit: AfterCommit) -> None:
    user = make_user(email="rina@example.com", email_verified_at=None)

    resend(make_ctx, after_commit, " Rina@Example.com ")

    assert EmailOtp.objects.filter(user=user).count() == 1
    assert mail.outbox[-1].to == ["rina@example.com"]


@pytest.mark.parametrize("email", ["verified@example.com", "nobody@example.com"])
def test_other_addresses_get_the_same_silent_answer(
    make_ctx: MakeCtx, after_commit: AfterCommit, email: str
) -> None:
    make_user(email="verified@example.com")

    resend(make_ctx, after_commit, email)

    assert mail.outbox == []


def test_one_resend_per_minute(make_ctx: MakeCtx, after_commit: AfterCommit) -> None:
    make_user(email="rina@example.com", email_verified_at=None)
    resend(make_ctx, after_commit, "rina@example.com")

    with pytest.raises(RateLimited) as error:
        resend(make_ctx, after_commit, "rina@example.com")

    assert error.value.retry_after_s == 60


def test_the_limit_applies_to_unknown_addresses_too(
    make_ctx: MakeCtx, after_commit: AfterCommit
) -> None:
    # Otherwise "429 only for registered emails" would reveal which ones exist
    resend(make_ctx, after_commit, "nobody@example.com")

    with pytest.raises(RateLimited):
        resend(make_ctx, after_commit, "nobody@example.com")


def test_at_most_five_per_hour(
    make_ctx: MakeCtx, after_commit: AfterCommit, frozen_clock: FrozenClock
) -> None:
    make_user(email="rina@example.com", email_verified_at=None)
    for _ in range(5):
        resend(make_ctx, after_commit, "rina@example.com")
        frozen_clock.advance(seconds=61)

    with pytest.raises(RateLimited):
        resend(make_ctx, after_commit, "rina@example.com")
    assert len(mail.outbox) == 5
