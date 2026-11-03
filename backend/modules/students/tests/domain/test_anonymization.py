import pytest

from core.emails import normalize_email
from core.errors import ConfirmationMismatch
from modules.students.domain.anonymization import (
    anonymized_email,
    anonymized_name,
    ensure_name_confirmed,
)


def test_placeholder_name_and_email() -> None:
    assert anonymized_name(7) == "Deleted student #7"
    assert anonymized_email(7) == "deleted-student-7@anonymized.invalid"


def test_placeholder_email_is_a_valid_but_unreachable_address() -> None:
    assert normalize_email(anonymized_email(7)).endswith(".invalid")


@pytest.mark.parametrize("typed", ["Rina Das", "  Rina   Das "])
def test_typing_the_name_confirms(typed: str) -> None:
    ensure_name_confirmed(typed, name="Rina Das")


@pytest.mark.parametrize("typed", ["", "rina das", "Rina", "Rina Dass"])
def test_anything_else_is_refused(typed: str) -> None:
    with pytest.raises(ConfirmationMismatch):
        ensure_name_confirmed(typed, name="Rina Das")
