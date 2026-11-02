from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from django.db import transaction

from core import mail
from core.context import Ctx, StudentStatus
from core.emails import mask_email
from core.rate_limit import RateLimit, ensure_within
from modules.identity import public as identity
from modules.students.repositories import students

# A whole class may sign up at once from the centre's one Wi-Fi address, so this is only
# a ceiling against floods; the per-address send limit protects inboxes (ADR-052)
PER_IP = RateLimit(limit=200, window=timedelta(hours=1))


@dataclass(frozen=True, slots=True)
class SignUpResult:
    email_masked: str


def sign_up_with_password(
    ctx: Ctx, *, name: str, email: str, password: str, client_ip: str
) -> SignUpResult:
    """Create an unverified student account and email it a code (domain_model.md §3.2, S-02).

    The answer never reveals whether the email is registered: the password rule is
    checked first either way, and for an existing address nothing is created. Its owner
    gets a fresh code if they never verified (they probably lost the first one), and a
    "someone tried to register" email otherwise. `email` is already normalized.
    """
    ensure_within(f"sign-up:ip:{client_ip}", PER_IP, now=ctx.now)
    identity.ensure_can_send_code(email, identity.OtpPurpose.VERIFY_EMAIL, now=ctx.now)
    identity.ensure_password_strong(password)
    existing = identity.find_user_id_by_email(email)
    if existing is None:
        try:
            _create_account(ctx, name=name, email=email, password=password)
        except identity.EmailTaken:
            # Another sign-up for this address won the race: treat it as existing
            existing = identity.find_user_id_by_email(email)
    if existing is not None:
        _answer_existing_owner(ctx, existing)
    return SignUpResult(email_masked=mask_email(email))


def _create_account(ctx: Ctx, *, name: str, email: str, password: str) -> None:
    with transaction.atomic():
        user_id = identity.create_student_user(ctx, email=email, name=name, password=password)
        students.insert_student(user_id, status=StudentStatus.UNVERIFIED)
        identity.issue_otp(ctx, user_id=user_id, purpose=identity.OtpPurpose.VERIFY_EMAIL)


def _answer_existing_owner(ctx: Ctx, user_id: UUID) -> None:
    owner = identity.get_user_summary(user_id)
    if not owner.email_verified:
        identity.issue_otp(ctx, user_id=user_id, purpose=identity.OtpPurpose.VERIFY_EMAIL)
        return
    mail.send(
        "students/email/account_exists",
        to=owner.email,
        context={"name": owner.name, "coaching_name": identity.PRODUCT_NAME},
    )
