from datetime import timedelta

from core.context import Ctx
from core.rate_limit import RateLimit, hit
from modules.identity.domain.values import OtpPurpose
from modules.identity.repositories import users
from modules.identity.services.commands.issue_otp import issue_otp

PER_EMAIL = RateLimit(limit=3, window=timedelta(hours=1))


def request_password_reset(ctx: Ctx, *, email: str) -> None:
    """Email a reset code to the account, if there is one (domain_model.md §3.1, S-04).

    The answer is always the same "if an account exists, we sent a code". Past 3 requests
    an hour for one address, nothing more is sent, silently (api_contract.md §5).
    `email` is already normalized.
    """
    if not hit(f"password-reset:email:{email}", PER_EMAIL, now=ctx.now).allowed:
        return
    user_id = users.find_user_id_by_email(email)
    if user_id is not None:
        issue_otp(ctx, user_id=user_id, purpose=OtpPurpose.RESET_PASSWORD)
