"""The database refuses bad identity rows, even if a service has a bug (database_schema §3.1)."""

from datetime import timedelta

import pytest
from django.db import IntegrityError, transaction

from core.clock import FrozenClock
from modules.identity.domain.values import OtpPurpose
from modules.identity.models import EmailOtp, User
from tests.factories.identity import make_user

pytestmark = pytest.mark.django_db


def refused(**fields: object) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        make_user(**fields)


def test_only_one_teacher_possible() -> None:
    make_user(teacher=True)

    refused(teacher=True, email="second.teacher@example.com")


def test_many_students_are_fine() -> None:
    for _ in range(3):
        make_user()

    assert User.objects.count() == 3


@pytest.mark.parametrize(
    "fields",
    [
        {"email": "Mixed.Case@Example.com"},
        {"name": ""},
        {"role": "ADMIN"},
    ],
    ids=["email-not-lowercase", "empty-name", "unknown-role"],
)
def test_invalid_user_is_refused(fields: dict[str, object]) -> None:
    refused(**fields)


def test_email_is_unique() -> None:
    make_user(email="same@example.com")

    refused(email="same@example.com")


def test_google_link_is_unique_but_optional() -> None:
    make_user(google_sub=None)
    make_user(google_sub=None)
    make_user(google_sub="google-123")

    refused(google_sub="google-123")


def new_otp(
    user: User,
    clock: FrozenClock,
    *,
    purpose: OtpPurpose = OtpPurpose.VERIFY_EMAIL,
    failed_tries: int = 0,
) -> EmailOtp:
    return EmailOtp.objects.create(
        user=user,
        purpose=purpose,
        code_hash="hash",
        expires_at=clock.now() + timedelta(minutes=10),
        failed_tries=failed_tries,
    )


def test_one_live_code_per_user_and_purpose(frozen_clock: FrozenClock) -> None:
    user = make_user()
    new_otp(user, frozen_clock)

    with pytest.raises(IntegrityError), transaction.atomic():
        new_otp(user, frozen_clock)


def test_new_code_allowed_once_the_old_one_is_superseded(frozen_clock: FrozenClock) -> None:
    user = make_user()
    old = new_otp(user, frozen_clock)
    EmailOtp.objects.filter(pk=old.pk).update(superseded_at=frozen_clock.now())

    new_otp(user, frozen_clock)
    new_otp(user, frozen_clock, purpose=OtpPurpose.RESET_PASSWORD)

    assert EmailOtp.objects.count() == 3


def test_failed_tries_stop_at_five(frozen_clock: FrozenClock) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        new_otp(make_user(), frozen_clock, failed_tries=6)
