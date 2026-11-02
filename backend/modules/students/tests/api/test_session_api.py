"""HTTP contract of login, session and profile (api_contract.md §2.1, screens S-01)."""

from collections.abc import Mapping
from datetime import timedelta
from typing import Any

import pytest
from django.test import Client

from core.clock import FrozenClock
from core.context import StudentStatus
from tests.factories.identity import make_user
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db
LOGIN = "/api/v1/auth/login"
SESSION = "/api/v1/auth/session"
PROFILE = "/api/v1/auth/profile"
PASSWORD = "correct-horse-battery"


def send(client: Client, method: str, path: str, body: Mapping[str, object]) -> Any:
    return getattr(client, method)(path, body, content_type="application/json")


def log_in(client: Client, email: str, password: str = PASSWORD) -> Any:
    return send(client, "post", LOGIN, {"email": email, "password": password})


def test_login_returns_the_session_user_and_a_cookie(
    client: Client, frozen_clock: FrozenClock
) -> None:
    make_student(email="rina@example.com", name="Rina Das")

    response = log_in(client, "rina@example.com")

    assert response.status_code == 200
    assert response.json() | {"id": "x"} == {
        "id": "x",
        "name": "Rina Das",
        "email": "rina@example.com",
        "role": "STUDENT",
        "status": "ACTIVE",
        "has_password": True,
        "performance_shared": False,
    }
    assert response.cookies["sessionid"]["httponly"]


def test_v1_f21_email_is_case_insensitive_at_login(
    client: Client, frozen_clock: FrozenClock
) -> None:
    make_student(email="rina@example.com")

    assert log_in(client, "  RINA@Example.COM ").status_code == 200


@pytest.mark.parametrize("email", ["rina@example.com", "nobody@example.com"])
def test_failed_login_is_one_generic_401(
    client: Client, frozen_clock: FrozenClock, email: str
) -> None:
    make_student(email="rina@example.com")

    response = log_in(client, email, "wrong-password")

    assert (response.status_code, response.json()["code"]) == (401, "invalid_credentials")
    assert "sessionid" not in response.cookies


def test_unverified_email_answers_403_with_the_masked_email(
    client: Client, frozen_clock: FrozenClock
) -> None:
    make_student(StudentStatus.UNVERIFIED, email="rina@example.com")

    response = log_in(client, "rina@example.com")

    assert (response.status_code, response.json()["code"]) == (403, "email_not_verified")
    assert response.json()["context"] == {"email_masked": "r•••@example.com"}


def test_pending_student_logs_in_to_see_their_status(
    client: Client, frozen_clock: FrozenClock
) -> None:
    make_student(StudentStatus.PENDING, email="rina@example.com")

    assert log_in(client, "rina@example.com").json()["status"] == "PENDING"


def test_session_key_rotates_on_login(client: Client, frozen_clock: FrozenClock) -> None:
    make_student(email="rina@example.com")
    client.get("/api/v1/auth/csrf")
    session = client.session
    session["planted"] = True
    session.save()
    planted_key = session.session_key

    log_in(client, "rina@example.com")

    assert client.cookies["sessionid"].value != planted_key


@pytest.mark.parametrize(
    ("teacher", "lifetime"), [(True, timedelta(days=7)), (False, timedelta(days=14))]
)
def test_session_lifetime_depends_on_the_role(
    client: Client, frozen_clock: FrozenClock, teacher: bool, lifetime: timedelta
) -> None:
    user = make_user(teacher=True) if teacher else make_student()

    log_in(client, user.email)

    # Django dates the expiry with the real clock, a moment before it is read back
    assert abs(client.session.get_expiry_age() - lifetime.total_seconds()) <= 2


def test_session_is_null_for_a_visitor(client: Client, frozen_clock: FrozenClock) -> None:
    assert client.get(SESSION).json() == {"user": None, "server_now": "2026-11-12T04:30:00Z"}


def test_session_names_the_logged_in_teacher(client: Client, frozen_clock: FrozenClock) -> None:
    teacher = make_user(teacher=True)
    log_in(client, teacher.email)

    user = client.get(SESSION).json()["user"]

    assert (user["role"], user["status"]) == ("TEACHER", None)


def test_profile_rename_returns_the_new_name(client: Client, frozen_clock: FrozenClock) -> None:
    make_student(email="rina@example.com")
    log_in(client, "rina@example.com")

    response = send(client, "patch", PROFILE, {"name": "  Rina   Das  "})

    assert (response.status_code, response.json()["name"]) == (200, "Rina Das")


def test_profile_needs_a_login(client: Client, frozen_clock: FrozenClock) -> None:
    response = send(client, "patch", PROFILE, {"name": "Someone"})

    assert (response.status_code, response.json()["code"]) == (401, "not_authenticated")
