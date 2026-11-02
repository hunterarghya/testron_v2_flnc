import pytest

from core.emails import InvalidEmail, mask_email, normalize_email


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [
        ("rina@gmail.com", "rina@gmail.com"),
        ("  Rina.Das@Gmail.COM ", "rina.das@gmail.com"),
        ("first+tag@sub.example.co.in", "first+tag@sub.example.co.in"),
    ],
)
def test_email_has_one_canonical_form(raw: str, normalized: str) -> None:
    assert normalize_email(raw) == normalized


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "rina",
        "rina@",
        "@gmail.com",
        "rina@gmail",
        "rina@gmail.",
        "ri na@gmail.com",
        "rina@@gmail.com",
        "a@b@c.com",
        "x" * 250 + "@gmail.com",
    ],
)
def test_malformed_email_is_rejected(raw: str) -> None:
    with pytest.raises(InvalidEmail):
        normalize_email(raw)


def test_invalid_email_is_also_a_value_error_for_request_validation() -> None:
    assert issubclass(InvalidEmail, ValueError)


@pytest.mark.parametrize(
    ("email", "masked"),
    [("rina@gmail.com", "r•••@gmail.com"), ("a@example.com", "a•••@example.com")],
)
def test_masked_email_hides_the_name(email: str, masked: str) -> None:
    assert mask_email(email) == masked
