"""request_password_reset + confirm_password_reset (domain_model.md §3.1, screens S-04)."""

import pytest
from django.core import mail

from conftest import AfterCommit, MakeCtx, last_emailed_code
from core.clock import FrozenClock
from modules.identity.domain.errors import OtpInvalid, PasswordTooWeak
from modules.identity.domain.values import OtpPurpose
from modules.identity.models import User, UserSession
from modules.identity.services.commands.confirm_password_reset import confirm_password_reset
from modules.identity.services.commands.consume_otp import consume_otp
from modules.identity.services.commands.request_password_reset import request_password_reset
from tests.factories.identity import make_user

pytestmark = pytest.mark.django_db
EMAIL = "rina@example.com"
NEW_PASSWORD = "a-brand-new-passphrase"


def request(make_ctx: MakeCtx, after_commit: AfterCommit, email: str = EMAIL) -> None:
    with after_commit():
        request_password_reset(make_ctx(), email=email)


def confirm(make_ctx: MakeCtx, code: str, password: str = NEW_PASSWORD) -> None:
    confirm_password_reset(
        make_ctx(), email=EMAIL, code=code, new_password=password, client_ip="ip"
    )


def test_reset_code_is_emailed(make_ctx: MakeCtx, after_commit: AfterCommit) -> None:
    make_user(email=EMAIL)

    request(make_ctx, after_commit)

    assert "password reset code" in mail.outbox[-1].subject


def test_unknown_email_gets_the_same_silent_answer(
    make_ctx: MakeCtx, after_commit: AfterCommit
) -> None:
    request(make_ctx, after_commit, "nobody@example.com")

    assert mail.outbox == []


def test_past_three_an_hour_nothing_more_is_sent(
    make_ctx: MakeCtx, after_commit: AfterCommit, frozen_clock: FrozenClock
) -> None:
    make_user(email=EMAIL)
    for _ in range(4):
        request(make_ctx, after_commit)
        frozen_clock.advance(minutes=1)

    assert len(mail.outbox) == 3


def test_code_and_new_password_set_the_password(
    make_ctx: MakeCtx, after_commit: AfterCommit
) -> None:
    make_user(email=EMAIL)
    request(make_ctx, after_commit)

    confirm(make_ctx, last_emailed_code())

    assert User.objects.get(email=EMAIL).check_password(NEW_PASSWORD)


def test_reset_ends_every_session(make_ctx: MakeCtx, after_commit: AfterCommit) -> None:
    user = make_user(email=EMAIL)
    UserSession.objects.create(
        session_key="a" * 32, session_data="", expire_date=make_ctx().now, user_id=user.id
    )
    request(make_ctx, after_commit)

    confirm(make_ctx, last_emailed_code())

    assert not UserSession.objects.filter(user_id=user.id).exists()


def test_weak_password_does_not_use_up_the_code(
    make_ctx: MakeCtx, after_commit: AfterCommit
) -> None:
    make_user(email=EMAIL)
    request(make_ctx, after_commit)
    code = last_emailed_code()

    with pytest.raises(PasswordTooWeak):
        confirm(make_ctx, code, password="short")
    confirm(make_ctx, code)


def test_v1_f01_reset_without_a_code_is_refused(
    make_ctx: MakeCtx, after_commit: AfterCommit
) -> None:
    make_user(email=EMAIL)
    request(make_ctx, after_commit)

    with pytest.raises(OtpInvalid):
        confirm(make_ctx, "")

    assert not User.objects.get(email=EMAIL).check_password(NEW_PASSWORD)


def test_unknown_email_cannot_confirm(make_ctx: MakeCtx) -> None:
    with pytest.raises(OtpInvalid):
        confirm(make_ctx, "123456")


def test_v1_f16_reset_code_cannot_verify_an_email(
    make_ctx: MakeCtx, after_commit: AfterCommit
) -> None:
    user = make_user(email=EMAIL, email_verified_at=None)
    request(make_ctx, after_commit)

    with pytest.raises(OtpInvalid):
        consume_otp(
            make_ctx(), user_id=user.id, purpose=OtpPurpose.VERIFY_EMAIL, code=last_emailed_code()
        )
