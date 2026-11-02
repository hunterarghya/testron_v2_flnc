import pytest

from core.config import Settings
from core.config_report import NOT_SET, SET, describe_settings

pytestmark = pytest.mark.usefixtures("environ")


@pytest.fixture
def environ(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)


def report(**values: object) -> dict[str, str]:
    settings = Settings(_env_file=None, django_env="build", **values)  # type: ignore[arg-type]
    return dict(describe_settings(settings))


def test_secrets_only_say_whether_they_are_set() -> None:
    shown = report(secret_key="super-secret-value", otp_hmac_key=None)

    assert shown["SECRET_KEY"] == SET
    assert shown["OTP_HMAC_KEY"] == NOT_SET
    assert "super-secret-value" not in str(shown)


def test_database_urls_are_hidden_because_they_hold_the_password() -> None:
    shown = report(database_url="postgres://app:hunter2@db:5432/app")

    assert shown["DATABASE_URL"] == SET
    assert "hunter2" not in str(shown)


def test_plain_settings_are_shown() -> None:
    shown = report(allowed_hosts=["a.example.com", "b.example.com"], teacher_name="Mrs Sen")

    assert shown["ALLOWED_HOSTS"] == "a.example.com, b.example.com"
    assert shown["TEACHER_NAME"] == "Mrs Sen"
    assert shown["DJANGO_ENV"] == "build"
    assert shown["GOOGLE_CLIENT_ID"] == NOT_SET


def test_every_setting_is_listed() -> None:
    assert len(report()) == len(Settings.model_fields)
