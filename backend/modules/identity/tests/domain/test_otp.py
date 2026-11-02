from datetime import UTC, datetime, timedelta

import pytest

from modules.identity.domain.otp import (
    LiveOtp,
    OtpCheck,
    check_code,
    hash_code,
    is_well_formed,
    tries_left_after_wrong,
)

NOW = datetime(2026, 11, 12, 4, 30, tzinfo=UTC)
KEY = b"test-key"
RIGHT = hash_code("482913", key=KEY)
WRONG = hash_code("000000", key=KEY)


def live(*, expires_in: timedelta = timedelta(minutes=5), failed_tries: int = 0) -> LiveOtp:
    return LiveOtp(code_hash=RIGHT, expires_at=NOW + expires_in, failed_tries=failed_tries)


@pytest.mark.parametrize(
    ("otp", "submitted", "outcome"),
    [
        (live(), RIGHT, OtpCheck.ACCEPTED),
        (live(), WRONG, OtpCheck.WRONG),
        (live(failed_tries=4), RIGHT, OtpCheck.ACCEPTED),
        (live(failed_tries=4), WRONG, OtpCheck.WRONG),
        (live(failed_tries=5), RIGHT, OtpCheck.UNUSABLE),
        (live(expires_in=timedelta(0)), RIGHT, OtpCheck.UNUSABLE),
        (live(expires_in=-timedelta(seconds=1)), RIGHT, OtpCheck.UNUSABLE),
        (None, RIGHT, OtpCheck.UNUSABLE),
    ],
    ids=[
        "right-code",
        "wrong-code-counts-a-try",
        "right-code-on-the-fifth-try",
        "fifth-wrong-try",
        "locked-after-five-wrong-tries",
        "expired-at-exactly-ten-minutes",
        "expired",
        "no-live-code",
    ],
)
def test_check_code(otp: LiveOtp | None, submitted: str, outcome: OtpCheck) -> None:
    assert check_code(otp, submitted_hash=submitted, now=NOW) is outcome


@pytest.mark.parametrize(
    ("code", "ok"),
    [
        ("482913", True),
        ("", False),
        ("48291", False),
        ("4829134", False),
        ("48291a", False),
        ("٤٨٢٩١٣", False),
        (" 48291", False),
    ],
    ids=["six-digits", "empty", "five", "seven", "letter", "arabic-digits", "space"],
)
def test_v1_f01_only_a_six_digit_code_can_be_checked(code: str, ok: bool) -> None:
    assert is_well_formed(code) is ok


def test_hash_depends_on_the_server_key() -> None:
    assert hash_code("482913", key=b"one") != hash_code("482913", key=b"two")


def test_hash_is_not_the_code() -> None:
    assert "482913" not in hash_code("482913", key=KEY)


@pytest.mark.parametrize(("failed", "left"), [(0, 4), (3, 1), (4, 0)])
def test_tries_left_after_a_wrong_code(failed: int, left: int) -> None:
    assert tries_left_after_wrong(live(failed_tries=failed)) == left
