import pytest

from conftest import MakeCtx
from core.context import Role
from modules.identity.domain.errors import PasswordTooWeak, TeacherEmailTaken
from modules.identity.models import User
from modules.identity.services.commands.seed_teacher import SeedTeacherResult, seed_teacher
from tests.factories.identity import make_user

pytestmark = pytest.mark.django_db
PASSWORD = "teacher-initial-passphrase"


def seed(
    make_ctx: MakeCtx,
    *,
    email: str = "teacher@example.com",
    name: str = "Mrs Sen",
    password: str | None = PASSWORD,
) -> SeedTeacherResult:
    return seed_teacher(make_ctx(), email=email, name=name, initial_password=password)


def teacher() -> User:
    return User.objects.get(role=Role.TEACHER)


def test_first_run_creates_a_ready_teacher(make_ctx: MakeCtx) -> None:
    result = seed(make_ctx, email="  Teacher@Example.com ")

    assert result.created
    created = teacher()
    assert (created.email, created.name, created.is_active) == (
        "teacher@example.com",
        "Mrs Sen",
        True,
    )
    assert created.email_verified_at is not None
    assert created.check_password(PASSWORD)


def test_v1_f19_teacher_only_via_seed_and_only_one(make_ctx: MakeCtx) -> None:
    seed(make_ctx)
    again = seed(make_ctx)

    assert not again.created
    assert User.objects.filter(role=Role.TEACHER).count() == 1


def test_later_runs_update_details_but_never_the_password(make_ctx: MakeCtx) -> None:
    seed(make_ctx)

    seed(
        make_ctx,
        email="new.teacher@example.com",
        name="Mrs Sen Gupta",
        password="other-pass-phrase",
    )

    updated = teacher()
    assert (updated.email, updated.name) == ("new.teacher@example.com", "Mrs Sen Gupta")
    assert updated.check_password(PASSWORD)


def test_without_an_initial_password_the_teacher_has_none(make_ctx: MakeCtx) -> None:
    seed(make_ctx, password=None)

    assert not teacher().has_usable_password()


def test_weak_initial_password_is_refused(make_ctx: MakeCtx) -> None:
    with pytest.raises(PasswordTooWeak):
        seed(make_ctx, password="short")

    assert not User.objects.exists()


def test_a_students_email_cannot_become_the_teacher(make_ctx: MakeCtx) -> None:
    make_user(email="teacher@example.com")

    with pytest.raises(TeacherEmailTaken):
        seed(make_ctx)

    assert not User.objects.filter(role=Role.TEACHER).exists()
