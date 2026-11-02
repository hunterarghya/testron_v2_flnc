"""HTTP contract of sign-up, verification and resend (api_contract.md §2.1)."""

from collections.abc import Mapping
from typing import Any

import pytest
from django.test import Client

from conftest import AfterCommit, last_emailed_code
from core.clock import FrozenClock

pytestmark = pytest.mark.django_db
SIGN_UP = "/api/v1/auth/sign-up"
VERIFY = "/api/v1/auth/email-verification"
RESEND = "/api/v1/auth/email-verification/resend"
FORM = {"name": "Rina Das", "email": "Rina@Example.com", "password": "a-long-passphrase"}


def post(client: Client, path: str, body: Mapping[str, object]) -> Any:
    return client.post(path, body, content_type="application/json")


def test_sign_up_is_accepted_with_a_masked_email(
    client: Client, after_commit: AfterCommit, frozen_clock: FrozenClock
) -> None:
    with after_commit():
        response = post(client, SIGN_UP, FORM)

    assert response.status_code == 202
    assert response.json() == {"email_masked": "r•••@example.com"}


@pytest.mark.parametrize(
    ("body", "field"),
    [
        (FORM | {"email": "not-an-email"}, "email"),
        (FORM | {"name": "   "}, "name"),
        (FORM | {"admin": True}, "admin"),
        ({"email": "rina@example.com", "password": "a-long-passphrase"}, "name"),
    ],
    ids=["bad-email", "blank-name", "unknown-field", "missing-name"],
)
def test_sign_up_shape_errors_name_the_field(
    client: Client, frozen_clock: FrozenClock, body: dict[str, object], field: str
) -> None:
    response = post(client, SIGN_UP, body)

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    assert field in [error["field"] for error in response.json()["errors"]]


def test_weak_password_has_its_own_code(client: Client, frozen_clock: FrozenClock) -> None:
    response = post(client, SIGN_UP, FORM | {"password": "short"})

    assert (response.status_code, response.json()["code"]) == (422, "password_too_weak")


def test_verification_logs_the_student_in(
    client: Client, after_commit: AfterCommit, frozen_clock: FrozenClock
) -> None:
    with after_commit():
        post(client, SIGN_UP, FORM)

    response = post(client, VERIFY, {"email": "rina@example.com", "code": last_emailed_code()})

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "STUDENT"
    assert body["status"] == "PENDING"
    assert body["has_password"] is True
    assert body["performance_shared"] is False
    assert "sessionid" in response.cookies
    assert response.cookies["sessionid"]["httponly"]


def test_wrong_code_is_otp_invalid_with_tries_left(
    client: Client, after_commit: AfterCommit, frozen_clock: FrozenClock
) -> None:
    with after_commit():
        post(client, SIGN_UP, FORM)
    wrong = "111111" if last_emailed_code() != "111111" else "222222"

    response = post(client, VERIFY, {"email": "rina@example.com", "code": wrong})

    assert response.status_code == 422
    assert response.json()["code"] == "otp_invalid"
    assert response.json()["context"] == {"tries_left": 4}
    assert "sessionid" not in response.cookies


def test_v1_f01_verification_without_a_code_is_otp_invalid(
    client: Client, after_commit: AfterCommit, frozen_clock: FrozenClock
) -> None:
    with after_commit():
        post(client, SIGN_UP, FORM)

    response = post(client, VERIFY, {"email": "rina@example.com"})

    assert (response.status_code, response.json()["code"]) == (422, "otp_invalid")


def test_resend_is_accepted_and_then_rate_limited(
    client: Client, after_commit: AfterCommit, frozen_clock: FrozenClock
) -> None:
    assert post(client, RESEND, {"email": "nobody@example.com"}).status_code == 202

    response = post(client, RESEND, {"email": "nobody@example.com"})

    assert response.status_code == 429
    assert response.json()["code"] == "rate_limited"
    assert response["Retry-After"] == "60"
