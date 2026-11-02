"""The environment rules that look at several settings together (used by `core.config`).

Each function returns a list of plain-language problems; an empty list means fine.
"""

from typing import TYPE_CHECKING

from pydantic import SecretStr

if TYPE_CHECKING:
    from core.config import Settings

_MIN_PROD_SECRET_KEY_LENGTH = 50
# Needed by every running app. `build` (collectstatic inside the image) has no secrets.
_ALWAYS_REQUIRED = ("secret_key", "database_url", "assignment_password_key", "otp_hmac_key")
_IMAGEKIT_REQUIRED = ("imagekit_public_key", "imagekit_private_key", "imagekit_url_endpoint")


def environment_problems(settings: "Settings") -> list[str]:
    return [*_missing_values(settings), *_unsafe_prod_values(settings), *_unpaired(settings)]


def _required_values(settings: "Settings") -> list[str]:
    if settings.django_env == "build":
        return []
    required = list(_ALWAYS_REQUIRED)
    if settings.django_env != "test":  # tests keep sent mail in memory
        required.append("email_url")
    if settings.media_backend == "imagekit":
        required.extend(_IMAGEKIT_REQUIRED)
    return required


def _missing_values(settings: "Settings") -> list[str]:
    return [
        f"{name.upper()} is required"
        for name in _required_values(settings)
        if not _is_set(getattr(settings, name))
    ]


def _unsafe_prod_values(settings: "Settings") -> list[str]:
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


def _unpaired(settings: "Settings") -> list[str]:
    if _is_set(settings.google_client_id) != _is_set(settings.google_client_secret):
        return ["GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set together"]
    return []


def _is_set(value: object) -> bool:
    if isinstance(value, SecretStr):
        return bool(value.get_secret_value())
    return bool(value)


def _secret_length(value: SecretStr | None) -> int:
    return len(value.get_secret_value()) if value else 0
