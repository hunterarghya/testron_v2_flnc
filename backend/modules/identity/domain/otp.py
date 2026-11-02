"""One-time email codes: how they are checked (domain_model.md §3.1, V1 F-01).

Pure rules. Generating the random code and storing it happen in the services.
"""

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from modules.identity.domain.values import MAX_OTP_FAILED_TRIES

OTP_LIFETIME = timedelta(minutes=10)
CODE_LENGTH = 6


class OtpCheck(StrEnum):
    ACCEPTED = "ACCEPTED"
    # A real try with a wrong code: it counts towards the limit
    WRONG = "WRONG"
    # No code can succeed: none live, expired, or already tried too often
    UNUSABLE = "UNUSABLE"


@dataclass(frozen=True, slots=True)
class LiveOtp:
    code_hash: str
    expires_at: datetime
    failed_tries: int


def is_well_formed(code: str) -> bool:
    """Exactly six ASCII digits. A missing or empty code is never accepted."""
    return len(code) == CODE_LENGTH and code.isascii() and code.isdigit()


def hash_code(code: str, *, key: bytes) -> str:
    """Codes are stored only as a keyed hash, so a database leak reveals no codes."""
    return hmac.new(key, code.encode("ascii"), hashlib.sha256).hexdigest()


def check_code(otp: LiveOtp | None, *, submitted_hash: str, now: datetime) -> OtpCheck:
    if otp is None or otp.expires_at <= now or otp.failed_tries >= MAX_OTP_FAILED_TRIES:
        return OtpCheck.UNUSABLE
    # Constant-time, so response timing can't reveal how much of a guess was right
    if hmac.compare_digest(otp.code_hash, submitted_hash):
        return OtpCheck.ACCEPTED
    return OtpCheck.WRONG


def tries_left_after_wrong(otp: LiveOtp) -> int:
    return max(0, MAX_OTP_FAILED_TRIES - otp.failed_tries - 1)
