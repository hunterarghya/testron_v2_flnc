from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.db import transaction

from core.context import Ctx
from core.rate_limit import RateLimit, ensure_within
from modules.identity.domain.errors import OtpInvalid
from modules.identity.domain.values import OtpPurpose
from modules.identity.repositories import sessions, users
from modules.identity.services.commands.consume_otp import consume_otp
from modules.identity.services.password_policy import ensure_password_strong

# Codes die after 5 wrong tries each; this is only a ceiling against floods (ADR-052)
PER_IP = RateLimit(limit=300, window=timedelta(minutes=10))


def confirm_password_reset(
    ctx: Ctx, *, email: str, code: str, new_password: str, client_ip: str
) -> None:
    """Set a new password with the emailed code; every session ends (domain_model.md §3.1, S-04).

    Both the code and the new password are required (V1 F-01). The password is checked
    first, so a weak one doesn't use up the code. An unknown email gets the same
    `otp_invalid` as a wrong code. `email` is already normalized.
    """
    ensure_within(f"password-reset-confirm:ip:{client_ip}", PER_IP, now=ctx.now)
    ensure_password_strong(new_password)
    user_id = users.find_user_id_by_email(email)
    if user_id is None:
        raise OtpInvalid()
    consume_otp(ctx, user_id=user_id, purpose=OtpPurpose.RESET_PASSWORD, code=code)
    with transaction.atomic():
        users.set_password_hash(user_id, make_password(new_password), now=ctx.now)
        sessions.delete_sessions_of(user_id)
