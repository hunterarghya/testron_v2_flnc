import secrets
from uuid import UUID

from django.db import transaction

from core import mail
from core.config import get_settings
from core.context import Ctx
from modules.identity.domain.otp import CODE_LENGTH, OTP_LIFETIME, hash_code
from modules.identity.domain.values import OtpPurpose
from modules.identity.repositories import email_otps, users

_TEMPLATES = {
    OtpPurpose.VERIFY_EMAIL: "identity/email/verify_email",
    OtpPurpose.RESET_PASSWORD: "identity/email/reset_password",
}
# Until the teacher's branding exists (Phase 2), emails use the product name (backlog O-11)
PRODUCT_NAME = "Test Platform"


def issue_otp(ctx: Ctx, *, user_id: UUID, purpose: OtpPurpose) -> None:
    """Create a fresh 6-digit code and email it (domain_model.md §3.1 #1, #4).

    Any earlier live code for the same purpose stops working. Only the code's keyed hash
    is stored. The email goes out after the transaction commits, so a rolled-back
    sign-up never sends a code for an account that doesn't exist.
    """
    code = "".join(secrets.choice("0123456789") for _ in range(CODE_LENGTH))
    user = users.get_user(user_id)
    email_otps.supersede_live_otps(user_id, purpose, now=ctx.now)
    email_otps.insert_otp(
        user_id,
        purpose,
        code_hash=hash_code(code, key=otp_key()),
        expires_at=ctx.now + OTP_LIFETIME,
        now=ctx.now,
    )
    context = {
        "name": user.name,
        "code": code,
        "coaching_name": PRODUCT_NAME,
        "expires_in_minutes": int(OTP_LIFETIME.total_seconds() // 60),
    }
    transaction.on_commit(lambda: mail.send(_TEMPLATES[purpose], to=user.email, context=context))


def otp_key() -> bytes:
    secret = get_settings().otp_hmac_key
    if secret is None:
        raise RuntimeError("OTP_HMAC_KEY is not configured")
    return secret.get_secret_value().encode()
