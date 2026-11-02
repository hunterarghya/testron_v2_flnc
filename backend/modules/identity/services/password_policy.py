"""The password rule shared by sign-up, reset and change: at least 8 characters and not a
common password (api_contract.md §1 `password_too_weak`). Django's validators do the checks.
"""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from modules.identity.domain.errors import PasswordTooWeak


def ensure_password_strong(password: str) -> None:
    try:
        validate_password(password)
    except ValidationError as error:
        raise PasswordTooWeak(" ".join(error.messages)) from None
