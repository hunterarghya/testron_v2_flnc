"""issue_otp and consume_otp: the life of one email code (domain_model.md §3.1)."""

from datetime import timedelta

import pytest
from django.core import mail
from django.db import transaction

from conftest import AfterCommit, MakeCtx, last_emailed_code
from core.clock import FrozenClock
from modules.identity.domain.errors import OtpInvalid
from modules.identity.domain.values import OtpPurpose
from modules.identity.models import EmailOtp, User
from modules.identity.services.commands.consume_otp import consume_otp
from modules.identity.services.commands.issue_otp import issue_otp
from tests.factories.identity import make_user

pytestmark = pytest.mark.django_db
VERIFY = OtpPurpose.VERIFY_EMAIL


def issue(make_ctx: MakeCtx, after_commit: AfterCommit, user: User) -> str:
    with after_commit():
        issue_otp(make_ctx(), user_id=user.id, purpose=VERIFY)
    return last_emailed_code()


def consume(make_ctx: MakeCtx, user: User, code: str) -> None:
    consume_otp(make_ctx(), user_id=user.id, purpose=VERIFY, code=code)


def test_code_is_emailed_and_only_its_hash_stored(
    make_ctx: MakeCtx, after_commit: AfterCommit
) -> None:
    user = make_user(email="rina@example.com")

    code = issue(make_ctx, after_commit, user)

    assert mail.outbox[-1].to == ["rina@example.com"]
    stored = EmailOtp.objects.get(user=user)
    assert code not in stored.code_hash
    assert len(stored.code_hash) == 64


def test_no_email_when_the_transaction_rolls_back(
    make_ctx: MakeCtx, after_commit: AfterCommit
) -> None:
    user = make_user()

    def sign_up_that_fails_after_issuing() -> None:
        with transaction.atomic():
            issue_otp(make_ctx(), user_id=user.id, purpose=VERIFY)
            raise RuntimeError("sign-up failed after the code was created")

    with after_commit(), pytest.raises(RuntimeError):
        sign_up_that_fails_after_issuing()

    assert mail.outbox == []


def test_code_expires_after_ten_minutes(
    make_ctx: MakeCtx, after_commit: AfterCommit, frozen_clock: FrozenClock
) -> None:
    user = make_user()
    issue(make_ctx, after_commit, user)

    assert EmailOtp.objects.get(user=user).expires_at == frozen_clock.now() + timedelta(minutes=10)


def test_right_code_is_used_up(make_ctx: MakeCtx, after_commit: AfterCommit) -> None:
    user = make_user()
    code = issue(make_ctx, after_commit, user)

    consume(make_ctx, user, code)

    assert EmailOtp.objects.get(user=user).consumed_at is not None
    with pytest.raises(OtpInvalid):
        consume(make_ctx, user, code)


def test_new_code_replaces_the_old_one(make_ctx: MakeCtx, after_commit: AfterCommit) -> None:
    user = make_user()
    old = issue(make_ctx, after_commit, user)
    new = issue(make_ctx, after_commit, user)

    if old != new:
        with pytest.raises(OtpInvalid):
            consume(make_ctx, user, old)
    consume(make_ctx, user, new)


def test_wrong_code_is_counted_even_though_it_is_refused(
    make_ctx: MakeCtx, after_commit: AfterCommit
) -> None:
    user = make_user()
    code = issue(make_ctx, after_commit, user)
    wrong = "111111" if code != "111111" else "222222"

    with pytest.raises(OtpInvalid) as error:
        consume(make_ctx, user, wrong)

    assert error.value.context == {"tries_left": 4}
    assert EmailOtp.objects.get(user=user).failed_tries == 1


def test_five_wrong_tries_kill_the_code(make_ctx: MakeCtx, after_commit: AfterCommit) -> None:
    user = make_user()
    code = issue(make_ctx, after_commit, user)
    wrong = "111111" if code != "111111" else "222222"
    for _ in range(5):
        with pytest.raises(OtpInvalid):
            consume(make_ctx, user, wrong)

    with pytest.raises(OtpInvalid) as error:
        consume(make_ctx, user, code)

    assert error.value.context == {}


def test_expired_code_is_refused(
    make_ctx: MakeCtx, after_commit: AfterCommit, frozen_clock: FrozenClock
) -> None:
    user = make_user()
    code = issue(make_ctx, after_commit, user)
    frozen_clock.advance(minutes=10)

    with pytest.raises(OtpInvalid):
        consume(make_ctx, user, code)


@pytest.mark.parametrize("code", ["", "12345", "abcdef"])
def test_v1_f01_missing_or_malformed_code_is_refused(
    make_ctx: MakeCtx, after_commit: AfterCommit, code: str
) -> None:
    user = make_user()
    issue(make_ctx, after_commit, user)

    with pytest.raises(OtpInvalid):
        consume(make_ctx, user, code)

    assert EmailOtp.objects.get(user=user).failed_tries == 0


def test_no_code_issued_means_refused(make_ctx: MakeCtx) -> None:
    with pytest.raises(OtpInvalid):
        consume(make_ctx, make_user(), "482913")


def test_a_code_cannot_be_checked_inside_another_transaction(
    make_ctx: MakeCtx, after_commit: AfterCommit
) -> None:
    # A wrong try would be rolled back with the caller's work and never count
    user = make_user()
    code = issue(make_ctx, after_commit, user)

    with pytest.raises(RuntimeError), transaction.atomic():
        consume(make_ctx, user, code)
