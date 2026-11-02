from datetime import timedelta
from uuid import UUID

from django.contrib.auth.hashers import make_password

from core.context import Ctx
from core.emails import mask_email
from core.rate_limit import RateLimit, ensure_within
from modules.identity.domain.errors import EmailNotVerified, InvalidCredentials
from modules.identity.repositories import users

# The real protection: guessing one account's password (api_contract.md §5)
PER_EMAIL = RateLimit(limit=10, window=timedelta(minutes=10))
# Only a ceiling against floods: a whole class logs in from the centre's one Wi-Fi (ADR-052)
PER_IP = RateLimit(limit=300, window=timedelta(minutes=10))


def authenticate_password(ctx: Ctx, *, email: str, password: str, client_ip: str) -> UUID:
    """Check an email and password; the id of the account they open (domain_model.md §3.1 #3).

    Every failure is one `invalid_credentials`. An unknown email still costs one password
    hash, so the response time doesn't reveal which emails exist. `email_not_verified`
    comes only after the password matched. `email` is already normalized.
    """
    ensure_within(f"login:ip:{client_ip}", PER_IP, now=ctx.now)
    ensure_within(f"login:email:{email}", PER_EMAIL, now=ctx.now)
    user = users.find_user_by_email(email)
    if user is None or not user.has_usable_password():
        make_password(password)
        raise InvalidCredentials()
    if not user.check_password(password):
        raise InvalidCredentials()
    if user.email_verified_at is None:
        raise EmailNotVerified(context={"email_masked": mask_email(user.email)})
    return user.id
