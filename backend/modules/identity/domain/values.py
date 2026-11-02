from enum import StrEnum


class OtpPurpose(StrEnum):
    VERIFY_EMAIL = "VERIFY_EMAIL"
    RESET_PASSWORD = "RESET_PASSWORD"  # noqa: S105  # a purpose name, not a password


# A code dies after this many wrong tries (domain_model.md §3.1)
MAX_OTP_FAILED_TRIES = 5
