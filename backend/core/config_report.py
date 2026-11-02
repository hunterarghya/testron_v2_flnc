"""The effective settings as `check_config` prints them: every value, except that secrets
only say whether they are set (dev_environment_and_deployment.md §8.3)."""

from pydantic import SecretStr

from core.config import Settings

SET = "(set)"
NOT_SET = "(not set)"


def describe_settings(settings: Settings) -> list[tuple[str, str]]:
    """(ENV_NAME, shown value) for every setting, in declaration order."""
    return [
        (name.upper(), _shown(getattr(settings, name), secret=_is_secret(name, settings)))
        for name in Settings.model_fields
    ]


def _is_secret(name: str, settings: Settings) -> bool:
    # Database URLs carry the password, so they are treated as secrets too
    return isinstance(getattr(settings, name), SecretStr) or name.startswith("database_url")


def _shown(value: object, *, secret: bool) -> str:
    if secret:
        return SET if _has_value(value) else NOT_SET
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or NOT_SET
    return NOT_SET if value is None or value == "" else str(value)


def _has_value(value: object) -> bool:
    if isinstance(value, SecretStr):
        return bool(value.get_secret_value())
    return bool(value)
