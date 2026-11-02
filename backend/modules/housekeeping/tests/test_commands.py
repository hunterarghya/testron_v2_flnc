from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from pydantic import SecretStr

from core.config import Settings, get_settings
from core.context import Role
from modules.housekeeping.management.commands import seed as seed_command
from modules.identity.public import find_user_id_by_email, get_user_summary

pytestmark = pytest.mark.django_db


def with_teacher_env(monkeypatch: pytest.MonkeyPatch, **values: object) -> None:
    configured: Settings = get_settings().model_copy(update=values)
    monkeypatch.setattr(seed_command, "get_settings", lambda: configured)


def run(command: str) -> str:
    output = StringIO()
    call_command(command, stdout=output)
    return output.getvalue()


def test_seed_creates_the_teacher_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    with_teacher_env(
        monkeypatch,
        teacher_email="teacher@example.com",
        teacher_name="Mrs Sen",
        teacher_initial_password=SecretStr("teacher-initial-passphrase"),
    )

    first, second = run("seed"), run("seed")

    assert "Teacher created" in first
    assert "already existed" in second
    teacher_id = find_user_id_by_email("teacher@example.com")
    assert teacher_id is not None
    assert get_user_summary(teacher_id).role is Role.TEACHER


def test_seed_explains_missing_teacher_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    with_teacher_env(monkeypatch, teacher_email=None, teacher_name=None)

    with pytest.raises(CommandError, match="TEACHER_EMAIL and TEACHER_NAME"):
        run("seed")


def test_check_config_lists_settings_without_secrets() -> None:
    output = run("check_config")

    assert "SECRET_KEY" in output
    assert "(set)" in output
    assert "test-only-secret-key" not in output
    assert "Configuration is valid" in output
