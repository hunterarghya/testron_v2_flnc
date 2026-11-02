import pytest

from conftest import MakeCtx
from core.context import Role
from modules.identity.domain.errors import EmailTaken, PasswordTooWeak
from modules.identity.models import User
from modules.identity.services.commands.create_student_user import create_student_user
from tests.factories.identity import make_user

pytestmark = pytest.mark.django_db


def create(
    make_ctx: MakeCtx,
    *,
    email: str = "rina@example.com",
    password: str = "a-long-passphrase",
    name: str = "Rina Das",
) -> User:
    user_id = create_student_user(make_ctx(), email=email, name=name, password=password)
    return User.objects.get(pk=user_id)


def test_new_account_is_an_inactive_unverified_student(make_ctx: MakeCtx) -> None:
    user = create(make_ctx)

    assert user.role == Role.STUDENT
    assert user.is_active is False
    assert user.email_verified_at is None


def test_password_is_stored_hashed(make_ctx: MakeCtx) -> None:
    user = create(make_ctx)

    assert "a-long-passphrase" not in user.password
    assert user.check_password("a-long-passphrase")


def test_name_is_cleaned(make_ctx: MakeCtx) -> None:
    right_to_left_override = chr(0x202E)

    assert create(make_ctx, name=f"  Rina {right_to_left_override}  Das ").name == "Rina Das"


@pytest.mark.parametrize("password", ["short", "password123", "12345678"])
def test_weak_password_is_refused(make_ctx: MakeCtx, password: str) -> None:
    with pytest.raises(PasswordTooWeak):
        create(make_ctx, password=password)

    assert not User.objects.exists()


def test_taken_email_is_reported_without_breaking_the_transaction(make_ctx: MakeCtx) -> None:
    make_user(email="rina@example.com")

    with pytest.raises(EmailTaken):
        create(make_ctx)

    assert User.objects.count() == 1
