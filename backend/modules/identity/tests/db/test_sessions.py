import pytest
from django.contrib.auth import SESSION_KEY

from modules.identity.models import UserSession
from modules.identity.sessions import SessionStore
from tests.factories.identity import make_user

pytestmark = pytest.mark.django_db


def test_session_row_records_the_logged_in_user() -> None:
    user = make_user()
    session = SessionStore()
    session[SESSION_KEY] = str(user.pk)

    session.save()

    assert UserSession.objects.get(session_key=session.session_key).user_id == user.pk


def test_anonymous_session_has_no_user() -> None:
    session = SessionStore()
    session["cart"] = "anything"

    session.save()

    assert UserSession.objects.get(session_key=session.session_key).user_id is None


def test_all_of_a_users_sessions_can_be_found_at_once() -> None:
    user = make_user()
    for _ in range(3):
        session = SessionStore()
        session[SESSION_KEY] = str(user.pk)
        session.save()

    assert UserSession.objects.filter(user_id=user.pk).count() == 3
