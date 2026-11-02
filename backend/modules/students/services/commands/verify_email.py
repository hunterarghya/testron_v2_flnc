from datetime import timedelta

from django.db import transaction

from core.context import Ctx
from core.rate_limit import RateLimit, ensure_within
from modules.identity import public as identity
from modules.students.domain.admission import status_after_email_verified
from modules.students.repositories import students
from modules.students.services.session_user import SessionUserView, build_session_user

# Codes already die after 5 wrong tries each. This is only a ceiling against one address
# guessing across many accounts, high enough for a whole class verifying at once (ADR-052)
PER_IP = RateLimit(limit=300, window=timedelta(minutes=10))


def verify_email(ctx: Ctx, *, email: str, code: str, client_ip: str) -> SessionUserView:
    """Confirm the email with its code; the account becomes PENDING (domain_model.md §7.1, S-03).

    An unknown address gets the same `otp_invalid` as a wrong code. The code is used up
    in its own transaction first (a wrong try must stay counted), then the email and the
    admission status change together. The controller then logs the student in.
    """
    ensure_within(f"verify-email:ip:{client_ip}", PER_IP, now=ctx.now)
    user_id = identity.find_user_id_by_email(email)
    if user_id is None:
        raise identity.OtpInvalid()
    identity.consume_otp(ctx, user_id=user_id, purpose=identity.OtpPurpose.VERIFY_EMAIL, code=code)
    with transaction.atomic():
        status_after_email_verified(students.get_status_for_update(user_id))
        identity.mark_email_verified(ctx, user_id=user_id)
        students.mark_pending(user_id, now=ctx.now)
    return build_session_user(user_id)
