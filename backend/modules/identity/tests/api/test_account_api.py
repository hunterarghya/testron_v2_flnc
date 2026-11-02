"""HTTP contract of CSRF, logout, password reset and password change (api_contract.md §2.1)."""

from collections.abc import Mapping
from typing import Any

import pytest
from django.test import Client

from conftest import AfterCommit, last_emailed_code
from core.clock import FrozenClock
from tests.factories.students import make_student

pytestmark = pytest.mark.django_db
EMAIL = "rina@example.com"
OLD, NEW = "correct-horse-battery", "a-brand-new-passphrase"


def post(client: Client, path: str, body: Mapping[str, object] | None = None) -> Any:
    return client.post(path, body or {}, content_type="application/json")


def logged_in(email: str = EMAIL, password: str = OLD) -> Client:
    client = Client()
    response = post(client, "/api/v1/auth/login", {"email": email, "password": password})
    assert response.status_code == 200
    return client


def is_logged_in(client: Client) -> bool:
    return client.get("/api/v1/auth/session").json()["user"] is not None


def test_csrf_endpoint_sets_the_cookie(client: Client) -> None:
    response = client.get("/api/v1/auth/csrf")

    assert response.status_code == 204
    assert response.cookies["csrftoken"].value


def test_logout_ends_this_session(frozen_clock: FrozenClock) -> None:
    make_student(email=EMAIL)
    client = logged_in()

    assert post(client, "/api/v1/auth/logout").status_code == 204
    assert not is_logged_in(client)


def test_logout_needs_a_login(client: Client) -> None:
    assert post(client, "/api/v1/auth/logout").status_code == 401


def test_password_reset_end_to_end(frozen_clock: FrozenClock, after_commit: AfterCommit) -> None:
    make_student(email=EMAIL)
    other_device = logged_in()
    client = Client()

    with after_commit():
        assert (
            post(client, "/api/v1/auth/password-reset", {"email": "Rina@Example.com"}).status_code
            == 202
        )
    confirm = {"email": EMAIL, "code": last_emailed_code(), "new_password": NEW}
    assert post(client, "/api/v1/auth/password-reset/confirm", confirm).status_code == 204

    assert not is_logged_in(other_device)
    logged_in(password=NEW)


def test_password_reset_for_an_unknown_email_looks_the_same(
    client: Client, frozen_clock: FrozenClock
) -> None:
    assert (
        post(client, "/api/v1/auth/password-reset", {"email": "nobody@example.com"}).status_code
        == 202
    )


def test_password_change_keeps_this_device_and_logs_out_others(frozen_clock: FrozenClock) -> None:
    make_student(email=EMAIL)
    this_device, other_device = logged_in(), logged_in()

    response = post(
        this_device, "/api/v1/auth/password", {"current_password": OLD, "new_password": NEW}
    )

    assert response.status_code == 204
    assert is_logged_in(this_device)
    assert not is_logged_in(other_device)


def test_wrong_current_password_is_403(frozen_clock: FrozenClock) -> None:
    make_student(email=EMAIL)

    response = post(
        logged_in(), "/api/v1/auth/password", {"current_password": "nope", "new_password": NEW}
    )

    assert (response.status_code, response.json()["code"]) == (403, "current_password_incorrect")
