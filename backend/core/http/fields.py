"""Request field types shared by every module's DTOs: validated and cleaned while parsing,
so a bad value is a 422 against that field (api_contract.md §0)."""

from typing import Annotated

from pydantic import AfterValidator, StringConstraints

from core.emails import MAX_EMAIL_LENGTH, normalize_email
from core.text import MAX_NAME_LENGTH, clean_text_line


def _clean_name(raw: str) -> str:
    name = clean_text_line(raw)
    if not name:
        raise ValueError("Enter a name")
    if len(name) > MAX_NAME_LENGTH:
        raise ValueError(f"Use at most {MAX_NAME_LENGTH} characters")
    return name


# An email, already in its one canonical form
EmailField = Annotated[
    str, StringConstraints(max_length=MAX_EMAIL_LENGTH + 20), AfterValidator(normalize_email)
]
# A person's name: hidden characters removed, spaces tidied, never empty
NameField = Annotated[
    str, StringConstraints(max_length=MAX_NAME_LENGTH * 2), AfterValidator(_clean_name)
]
# Long enough for any passphrase, short enough that hashing it can't be used to stall the server
PasswordField = Annotated[str, StringConstraints(max_length=128)]
