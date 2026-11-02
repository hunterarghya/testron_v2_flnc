import pytest

from core.config import ConfigError, Settings, load_settings

VALID_FERNET_KEY = "dGVzdC1vbmx5LWFzc2lnbm1lbnQtcHcta2V5LTAwMDE="
LONG_SECRET = "s" * 50

DEV_ENV = {
    "DJANGO_ENV": "dev",
    "SECRET_KEY": "dev-secret",
    "DATABASE_URL": "postgres://app:app@localhost:5432/app",
    "ASSIGNMENT_PASSWORD_KEY": VALID_FERNET_KEY,
    "OTP_HMAC_KEY": "dev-otp-key",
    "EMAIL_URL": "smtp://localhost:1025",
    "MEDIA_BACKEND": "local",
}

PROD_ENV = {
    **DEV_ENV,
    "DJANGO_ENV": "prod",
    "SECRET_KEY": LONG_SECRET,
    "ALLOWED_HOSTS": "tests.example.com",
    "CSRF_TRUSTED_ORIGINS": "https://tests.example.com",
    "MEDIA_BACKEND": "imagekit",
    "IMAGEKIT_PUBLIC_KEY": "public_test",
    "IMAGEKIT_PRIVATE_KEY": "private_test",
    "IMAGEKIT_URL_ENDPOINT": "https://ik.imagekit.io/example",
}


@pytest.fixture
def environ(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """An environment with none of our variables set (pytest-env sets some)."""
    for name in Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)
    return monkeypatch


def load(environ: pytest.MonkeyPatch, values: dict[str, str]) -> Settings:
    for name, value in values.items():
        environ.setenv(name, value)
    return load_settings(env_file=None)


def without(values: dict[str, str], name: str) -> dict[str, str]:
    return {key: value for key, value in values.items() if key != name}


def test_dev_settings_load_from_environment(environ: pytest.MonkeyPatch) -> None:
    settings = load(environ, DEV_ENV)

    assert settings.django_env == "dev"
    assert settings.media_backend == "local"


def test_v1_f15_boot_fails_without_secret_key(environ: pytest.MonkeyPatch) -> None:
    with pytest.raises(ConfigError, match="SECRET_KEY is required"):
        load(environ, without(PROD_ENV, "SECRET_KEY"))


def test_v1_f15_debug_defaults_false(environ: pytest.MonkeyPatch) -> None:
    assert load(environ, DEV_ENV).debug is False


def test_environment_defaults_to_prod_rules(environ: pytest.MonkeyPatch) -> None:
    with pytest.raises(ConfigError, match="SECRET_KEY must be at least 50"):
        load(environ, without(DEV_ENV, "DJANGO_ENV") | {"MEDIA_BACKEND": "imagekit"})


def test_empty_value_counts_as_missing(environ: pytest.MonkeyPatch) -> None:
    with pytest.raises(ConfigError, match="OTP_HMAC_KEY is required"):
        load(environ, DEV_ENV | {"OTP_HMAC_KEY": ""})


def test_every_missing_value_is_reported_at_once(environ: pytest.MonkeyPatch) -> None:
    with pytest.raises(ConfigError) as error:
        load(environ, {"DJANGO_ENV": "dev", "MEDIA_BACKEND": "local"})

    for name in ("SECRET_KEY", "DATABASE_URL", "ASSIGNMENT_PASSWORD_KEY", "OTP_HMAC_KEY"):
        assert f"{name} is required" in str(error.value)


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"DEBUG": "True"}, "DEBUG must be False in prod"),
        ({"SECRET_KEY": "short"}, "SECRET_KEY must be at least 50"),
        ({"MEDIA_BACKEND": "local"}, "MEDIA_BACKEND must be imagekit in prod"),
        ({"ALLOWED_HOSTS": ""}, "ALLOWED_HOSTS is required in prod"),
        ({"CSRF_TRUSTED_ORIGINS": ""}, "CSRF_TRUSTED_ORIGINS is required in prod"),
        ({"E2E_TEST_HOOKS": "1"}, "E2E_TEST_HOOKS must be off in prod"),
        ({"IMAGEKIT_PRIVATE_KEY": ""}, "IMAGEKIT_PRIVATE_KEY is required"),
    ],
    ids=["debug", "short-secret", "local-media", "hosts", "csrf-origins", "e2e-hooks", "imagekit"],
)
def test_prod_refuses_unsafe_value(
    environ: pytest.MonkeyPatch, override: dict[str, str], message: str
) -> None:
    with pytest.raises(ConfigError, match=message):
        load(environ, PROD_ENV | override)


def test_prod_settings_load_when_complete(environ: pytest.MonkeyPatch) -> None:
    assert load(environ, PROD_ENV).django_env == "prod"


def test_image_build_needs_no_secrets(environ: pytest.MonkeyPatch) -> None:
    assert load(environ, {"DJANGO_ENV": "build"}).secret_key is None


def test_test_environment_needs_no_email_url(environ: pytest.MonkeyPatch) -> None:
    settings = load(environ, without(DEV_ENV, "EMAIL_URL") | {"DJANGO_ENV": "test"})

    assert settings.email_url is None


def test_comma_lists_are_split_and_trimmed(environ: pytest.MonkeyPatch) -> None:
    settings = load(environ, DEV_ENV | {"ALLOWED_HOSTS": " localhost, 127.0.0.1 ,"})

    assert settings.allowed_hosts == ["localhost", "127.0.0.1"]


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("ASSIGNMENT_PASSWORD_KEY", "not-a-fernet-key"),
        ("ASSIGNMENT_PASSWORD_KEY", f"{VALID_FERNET_KEY},broken"),
        ("DATABASE_URL", "mysql://app:app@localhost/app"),
        ("EMAIL_URL", "http://localhost:1025"),
        ("BACKOFFICE_PATH", "../admin"),
    ],
)
def test_malformed_value_is_rejected(environ: pytest.MonkeyPatch, name: str, value: str) -> None:
    with pytest.raises(ConfigError, match=name):
        load(environ, DEV_ENV | {name: value})


def test_several_fernet_keys_are_accepted_for_rotation(environ: pytest.MonkeyPatch) -> None:
    keys = f"{VALID_FERNET_KEY}, {VALID_FERNET_KEY}"

    assert load(environ, DEV_ENV | {"ASSIGNMENT_PASSWORD_KEY": keys}).assignment_password_key


def test_google_keys_must_come_together(environ: pytest.MonkeyPatch) -> None:
    with pytest.raises(ConfigError, match="GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"):
        load(environ, DEV_ENV | {"GOOGLE_CLIENT_ID": "client-id"})


def test_error_message_never_shows_secret_values(environ: pytest.MonkeyPatch) -> None:
    secret = "do-not-print-this-key"

    with pytest.raises(ConfigError) as error:
        load(environ, DEV_ENV | {"ASSIGNMENT_PASSWORD_KEY": secret})

    assert secret not in str(error.value)
    assert error.value.__cause__ is None
