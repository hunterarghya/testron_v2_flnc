import pytest
from django.core import mail

from conftest import AfterCommit, MakeCtx
from core.context import Role, StudentStatus
from core.errors import RateLimited
from modules.identity import public as identity_public
from modules.identity.public import PasswordTooWeak, find_user_id_by_email, get_user_summary
from modules.students.models import Student
from modules.students.services.commands.sign_up_with_password import (
    SignUpResult,
    sign_up_with_password,
)
from tests.factories.identity import make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db


def sign_up(
    make_ctx: MakeCtx,
    after_commit: AfterCommit,
    *,
    email: str = "rina@example.com",
    password: str = "a-long-passphrase",
    ip: str = "10.0.0.1",
) -> SignUpResult:
    with after_commit():
        return sign_up_with_password(
            make_ctx(), name="Rina Das", email=email, password=password, client_ip=ip
        )


def test_new_account_is_unverified_and_gets_a_code(
    make_ctx: MakeCtx, after_commit: AfterCommit
) -> None:
    result = sign_up(make_ctx, after_commit)

    user_id = find_user_id_by_email("rina@example.com")
    assert user_id is not None
    assert Student.objects.get(user_id=user_id).status == StudentStatus.UNVERIFIED
    assert "verification code" in mail.outbox[-1].subject
    assert result.email_masked == "r•••@example.com"


def test_existing_account_owner_is_told_and_nothing_changes(
    make_ctx: MakeCtx, after_commit: AfterCommit
) -> None:
    make_student(email="rina@example.com")

    result = sign_up(make_ctx, after_commit)

    assert Student.objects.count() == 1
    assert "tried to create" in mail.outbox[-1].subject
    assert result.email_masked == "r•••@example.com"


def test_unverified_owner_signing_up_again_gets_a_fresh_code(
    make_ctx: MakeCtx, after_commit: AfterCommit
) -> None:
    make_student(StudentStatus.UNVERIFIED, email="rina@example.com")

    sign_up(make_ctx, after_commit)

    assert Student.objects.count() == 1
    assert "verification code" in mail.outbox[-1].subject


def test_teacher_email_cannot_sign_up(make_ctx: MakeCtx, after_commit: AfterCommit) -> None:
    teacher = make_user(teacher=True)

    sign_up(make_ctx, after_commit, email=teacher.email)

    assert get_user_summary(teacher.id).role is Role.TEACHER
    assert not Student.objects.exists()
    assert "tried to create" in mail.outbox[-1].subject


def test_weak_password_is_refused_even_for_a_registered_email(
    make_ctx: MakeCtx, after_commit: AfterCommit
) -> None:
    # Checking it only for new emails would reveal which ones are registered
    make_student(email="rina@example.com")

    with pytest.raises(PasswordTooWeak):
        sign_up(make_ctx, after_commit, password="short")

    assert mail.outbox == []


def test_ten_sign_ups_per_hour_from_one_address(
    make_ctx: MakeCtx, after_commit: AfterCommit
) -> None:
    for number in range(10):
        sign_up(make_ctx, after_commit, email=f"s{number}@example.com")

    with pytest.raises(RateLimited):
        sign_up(make_ctx, after_commit, email="eleventh@example.com")


def test_repeated_sign_ups_cannot_flood_one_inbox(
    make_ctx: MakeCtx, after_commit: AfterCommit
) -> None:
    make_student(email="rina@example.com")
    sign_up(make_ctx, after_commit)

    with pytest.raises(RateLimited):
        sign_up(make_ctx, after_commit, ip="10.0.0.2")

    assert len(mail.outbox) == 1


def test_losing_a_sign_up_race_is_answered_like_an_existing_account(
    make_ctx: MakeCtx, after_commit: AfterCommit, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The other sign-up commits between our "is it taken?" check and our insert
    make_student(email="rina@example.com")
    real_lookup = identity_public.find_user_id_by_email
    lookups = iter([None])
    monkeypatch.setattr(
        identity_public,
        "find_user_id_by_email",
        lambda email: next(lookups, real_lookup(email)),
    )

    result = sign_up(make_ctx, after_commit)

    assert Student.objects.count() == 1
    assert "tried to create" in mail.outbox[-1].subject
    assert result.email_masked == "r•••@example.com"
