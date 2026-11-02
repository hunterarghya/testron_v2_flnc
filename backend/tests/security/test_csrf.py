"""CSRF (security.md §4.1): every unsafe API operation refuses a request without the token,
logged in or not; with the token from /auth/csrf it goes through."""

import pytest
from django.test import Client

from tests.factories.identity import make_user
from tests.factories.students import make_student
from tests.security.operations import Operation, all_operations

pytestmark = pytest.mark.django_db
UNSAFE = [operation for operation in all_operations() if operation.is_unsafe]


def csrf_client(*, as_teacher: bool) -> Client:
    # Django's test client skips CSRF unless asked to enforce it, like a browser would
    client = Client(enforce_csrf_checks=True)
    if as_teacher:
        client.force_login(make_user(teacher=True))
    return client


def call(client: Client, operation: Operation, **headers: str) -> object:
    return getattr(client, operation.method.lower())(
        operation.url(), {}, content_type="application/json", headers=headers
    )


@pytest.mark.parametrize("as_teacher", [False, True], ids=["anonymous", "teacher"])
@pytest.mark.parametrize("operation", UNSAFE, ids=lambda op: op.key)
def test_unsafe_methods_require_csrf(operation: Operation, as_teacher: bool) -> None:
    response = call(csrf_client(as_teacher=as_teacher), operation)

    assert response.status_code == 403  # type: ignore[attr-defined]
    assert response.json()["code"] == "csrf_failed"  # type: ignore[attr-defined]


def test_the_token_from_the_csrf_endpoint_lets_a_login_through() -> None:
    make_student(email="rina@example.com")
    client = Client(enforce_csrf_checks=True)
    token = client.get("/api/v1/auth/csrf").cookies["csrftoken"].value

    response = client.post(
        "/api/v1/auth/login",
        {"email": "rina@example.com", "password": "correct-horse-battery"},
        content_type="application/json",
        headers={"X-CSRFToken": token},
    )

    assert response.status_code == 200


def test_reads_never_need_the_token() -> None:
    assert Client(enforce_csrf_checks=True).get("/api/v1/auth/session").status_code == 200
