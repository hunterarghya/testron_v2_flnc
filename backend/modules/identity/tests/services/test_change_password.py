import pytest

from conftest import MakeCtx
from core.context import Actor, Role
from core.errors import NotAuthenticated
from modules.identity.domain.errors import CurrentPasswordIncorrect, PasswordTooWeak
from modules.identity.models import User
from modules.identity.services.commands.change_password import change_password
from tests.factories.identity import make_user

pytestmark = pytest.mark.django_db
NEW = "a-brand-new-passphrase"


def change(make_ctx: MakeCtx, user: User, current: str | None, new: str = NEW) -> None:
    actor = Actor(user_id=user.id, role=Role.STUDENT)
    change_password(make_ctx(actor), current_password=current, new_password=new)


def stored(user: User) -> User:
    return User.objects.get(pk=user.pk)


def test_right_current_password_allows_the_change(make_ctx: MakeCtx) -> None:
    user = make_user()

    change(make_ctx, user, "correct-horse-battery")

    assert stored(user).check_password(NEW)


@pytest.mark.parametrize("current", ["wrong-password", None, ""])
def test_wrong_or_missing_current_password_is_refused(
    make_ctx: MakeCtx, current: str | None
) -> None:
    user = make_user()

    with pytest.raises(CurrentPasswordIncorrect):
        change(make_ctx, user, current)

    assert stored(user).check_password("correct-horse-battery")


def test_google_only_account_sets_a_first_password(make_ctx: MakeCtx) -> None:
    user = make_user(google_only=True)

    change(make_ctx, user, None)

    assert stored(user).check_password(NEW)


def test_weak_new_password_is_refused(make_ctx: MakeCtx) -> None:
    with pytest.raises(PasswordTooWeak):
        change(make_ctx, make_user(), "correct-horse-battery", new="short")


def test_visitor_cannot_change_a_password(make_ctx: MakeCtx) -> None:
    with pytest.raises(NotAuthenticated):
        change_password(make_ctx(), current_password=None, new_password=NEW)
