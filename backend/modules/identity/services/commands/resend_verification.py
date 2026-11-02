from core.context import Ctx
from core.emails import normalize_email
from modules.identity.domain.values import OtpPurpose
from modules.identity.repositories import users
from modules.identity.services.commands.issue_otp import issue_otp
from modules.identity.services.otp_sending import ensure_can_send_code


def resend_verification(ctx: Ctx, *, email: str) -> None:
    """Email a new verification code to an unverified account (domain_model.md §3.1 #5).

    The answer is the same for every address (registered or not, verified or not), so
    it can't be used to discover accounts. At most 1 per 60 s and 5 per hour per address.
    """
    email = normalize_email(email)
    ensure_can_send_code(email, OtpPurpose.VERIFY_EMAIL, now=ctx.now)
    user_id = users.find_user_id_by_email(email)
    if user_id is None or users.get_user(user_id).email_verified_at is not None:
        return
    issue_otp(ctx, user_id=user_id, purpose=OtpPurpose.VERIFY_EMAIL)
