"""Typed application settings, read once from the environment and checked at boot.

A missing or unsafe value stops the app from starting with a message that names the
variable but never shows its value (dev_environment_and_deployment.md §2.1, V1 F-15).
"""

import os
from base64 import urlsafe_b64decode
from functools import cache
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, SecretStr, ValidationError, field_validator, model_validator
from pydantic_core import ErrorDetails
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

Environment = Literal["dev", "test", "build", "prod"]
MediaBackend = Literal["local", "imagekit"]
CommaList = Annotated[list[str], NoDecode]

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
EMAIL_SCHEMES = ("smtp", "smtp+tls", "smtp+ssl")
_POSTGRES_SCHEMES = ("postgres://", "postgresql://")
_MIN_PROD_SECRET_KEY_LENGTH = 50
_FERNET_KEY_BYTES = 32

# Needed by every running app. `build` (collectstatic inside the image) has no secrets.
_ALWAYS_REQUIRED = ("secret_key", "database_url", "assignment_password_key", "otp_hmac_key")
_IMAGEKIT_REQUIRED = ("imagekit_public_key", "imagekit_private_key", "imagekit_url_endpoint")


class ConfigError(Exception):
    """The environment is missing a value or holds an unsafe one."""


class Settings(BaseSettings):
    # Empty values (`KEY=`) count as unset, so they fall back to the defaults below
    model_config = SettingsConfigDict(extra="ignore", frozen=True, env_ignore_empty=True)

    # Safe by default: forgetting DJANGO_ENV gives the strictest rules
    django_env: Environment = "prod"
    debug: bool = False
    secret_key: SecretStr | None = None
    allowed_hosts: CommaList = Field(default_factory=list)
    csrf_trusted_origins: CommaList = Field(default_factory=list)
    backoffice_path: str = Field(default="backoffice", pattern=r"^[a-z0-9][a-z0-9-]{2,63}$")

    database_url: str | None = None
    database_url_direct: str | None = None

    teacher_email: str | None = None
    teacher_name: str | None = None
    teacher_initial_password: SecretStr | None = None

    assignment_password_key: SecretStr | None = None
    otp_hmac_key: SecretStr | None = None

    email_url: str | None = None
    email_from: str = "noreply@localhost"

    media_backend: MediaBackend = "imagekit"
    imagekit_public_key: str | None = None
    imagekit_private_key: SecretStr | None = None
    imagekit_url_endpoint: str | None = None

    google_client_id: str | None = None
    google_client_secret: SecretStr | None = None

    sentry_dsn: str | None = None
    e2e_test_hooks: bool = False

    @field_validator("allowed_hosts", "csrf_trusted_origins", mode="before")
    @classmethod
    def _split_commas(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("database_url", "database_url_direct")
    @classmethod
    def _check_postgres_url(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith(_POSTGRES_SCHEMES):
            raise ValueError("must be a postgres:// URL")
        return value

    @field_validator("email_url")
    @classmethod
    def _check_email_url(cls, value: str | None) -> str | None:
        if value is not None and value.partition("://")[0] not in EMAIL_SCHEMES:
            raise ValueError(f"must start with one of {', '.join(EMAIL_SCHEMES)}://")
        return value

    @field_validator("assignment_password_key")
    @classmethod
    def _check_fernet_keys(cls, value: SecretStr | None) -> SecretStr | None:
        keys = value.get_secret_value().split(",") if value else []
        if not all(_is_fernet_key(key.strip()) for key in keys):
            raise ValueError("must be comma-separated Fernet keys (32 url-safe base64 bytes)")
        return value

    @model_validator(mode="after")
    def _check_environment_rules(self) -> Self:
        problems = [*_missing_values(self), *_unsafe_prod_values(self), *_unpaired_values(self)]
        if problems:
            raise ValueError("; ".join(problems))
        return self


def load_settings(*, env_file: Path | None) -> Settings:
    """Read the environment (plus `env_file` if given) into validated settings."""
    try:
        return Settings(_env_file=env_file)
    except ValidationError as error:
        # `from None` drops pydantic's own message, which would print the rejected values
        raise ConfigError(_describe(error)) from None


@cache
def get_settings() -> Settings:
    """The process-wide settings, read once."""
    return load_settings(env_file=_env_file_for(os.environ.get("DJANGO_ENV")))


def _env_file_for(django_env: str | None) -> Path | None:
    # Tests must not depend on a developer's local .env
    return None if django_env == "test" else ENV_FILE


def _required_values(settings: Settings) -> list[str]:
    if settings.django_env == "build":
        return []
    required = list(_ALWAYS_REQUIRED)
    if settings.django_env != "test":  # tests keep sent mail in memory
        required.append("email_url")
    if settings.media_backend == "imagekit":
        required.extend(_IMAGEKIT_REQUIRED)
    return required


def _missing_values(settings: Settings) -> list[str]:
    return [
        f"{name.upper()} is required"
        for name in _required_values(settings)
        if not _is_set(getattr(settings, name))
    ]


def _unsafe_prod_values(settings: Settings) -> list[str]:
    if settings.django_env != "prod":
        return []
    rules = {
        "DEBUG must be False in prod": settings.debug,
        f"SECRET_KEY must be at least {_MIN_PROD_SECRET_KEY_LENGTH} characters in prod": (
            _secret_length(settings.secret_key) < _MIN_PROD_SECRET_KEY_LENGTH
        ),
        "MEDIA_BACKEND must be imagekit in prod": settings.media_backend != "imagekit",
        "ALLOWED_HOSTS is required in prod": not settings.allowed_hosts,
        "CSRF_TRUSTED_ORIGINS is required in prod": not settings.csrf_trusted_origins,
        "E2E_TEST_HOOKS must be off in prod": settings.e2e_test_hooks,
    }
    return [message for message, broken in rules.items() if broken]


def _unpaired_values(settings: Settings) -> list[str]:
    if _is_set(settings.google_client_id) != _is_set(settings.google_client_secret):
        return ["GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set together"]
    return []


def _is_set(value: object) -> bool:
    if isinstance(value, SecretStr):
        return bool(value.get_secret_value())
    return bool(value)


def _secret_length(value: SecretStr | None) -> int:
    return len(value.get_secret_value()) if value else 0


def _is_fernet_key(key: str) -> bool:
    try:
        return len(urlsafe_b64decode(key.encode("ascii"))) == _FERNET_KEY_BYTES
    except ValueError:  # bad base64 or non-ASCII text
        return False


def _describe(error: ValidationError) -> str:
    problems = [_describe_one(detail) for detail in error.errors(include_input=False)]
    return "Invalid configuration: " + "; ".join(problems)


def _describe_one(detail: ErrorDetails) -> str:
    message = detail["msg"].removeprefix("Value error, ")
    if not detail["loc"]:  # a rule across several values
        return message
    return f"{str(detail['loc'][0]).upper()}: {message}"
