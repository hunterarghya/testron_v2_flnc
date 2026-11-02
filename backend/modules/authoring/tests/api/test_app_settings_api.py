"""HTTP contract of /app and /admin/settings (api_contract.md §2.1, §2.2)."""

import pytest
from django.test import Client

from core.clock import FrozenClock
from tests.clients import logged_in, send
from tests.factories.identity import make_user

pytestmark = pytest.mark.django_db
SETTINGS = "/api/v1/admin/settings"


@pytest.fixture
def teacher(frozen_clock: FrozenClock) -> Client:
    return logged_in(make_user(teacher=True).email)


def test_anyone_reads_the_branding() -> None:
    assert Client().get("/api/v1/app").json() == {
        "coaching_name": "Test Platform",
        "logo_url": None,
    }


def test_settings_carry_marks_as_decimal_strings(teacher: Client) -> None:
    body = teacher.get(SETTINGS).json()

    assert body == {
        "coaching_name": "Test Platform",
        "logo_url": None,
        "default_marks": "4.00",
        "default_negative_marks": "1.00",
        "default_integrity_grace_s": 5,
        "default_integrity_max_warnings": 3,
        "default_integrity_action": "AUTO_SUBMIT",
        "updated_at": None,
    }


def test_patch_changes_only_what_is_sent(teacher: Client) -> None:
    body = send(teacher, "patch", SETTINGS, {"default_marks": "2.5", "coaching_name": "Bio"}).json()

    assert (body["default_marks"], body["default_negative_marks"]) == ("2.50", "1.00")
    assert body["coaching_name"] == "Bio"
    assert Client().get("/api/v1/app").json()["coaching_name"] == "Bio"


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"default_marks": "0"}, "default_marks"),
        ({"default_marks": "1.234"}, "default_marks"),
        ({"default_integrity_grace_s": 61}, "default_integrity_grace_s"),
        ({"default_integrity_action": "WARN"}, "default_integrity_action"),
        ({"logo_url": "https://tracker.example/a.png"}, "logo_url"),
    ],
)
def test_bad_values_are_field_errors(
    teacher: Client, change: dict[str, object], field: str
) -> None:
    response = send(teacher, "patch", SETTINGS, change)

    assert response.status_code == 422
    assert field in [error["field"] for error in response.json()["errors"]]


def test_unknown_fields_are_refused(teacher: Client) -> None:
    assert send(teacher, "patch", SETTINGS, {"time_zone": "UTC"}).status_code == 422
