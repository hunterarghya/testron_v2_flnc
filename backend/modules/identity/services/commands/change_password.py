from datetime import timedelta

from django.contrib.auth.hashers import make_password

from core.context import Ctx
from core.errors import NotAuthenticated
from core.rate_limit import RateLimit, ensure_within
from modules.identity.domain.errors import CurrentPasswordIncorrect
from modules.identity.repositories import users
from modules.identity.services.password_policy import ensure_password_strong

# Someone with a borrowed, unlocked laptop can't try current passwords endlessly
PER_USER = RateLimit(limit=10, window=timedelta(minutes=10))


def change_password(ctx: Ctx, *, current_password: str | None, new_password: str) -> None:
    """Change your own password (api_contract.md §2.1, P-11, T-19).

    The current password is required when the account has one; a Google-only account
    sets its first password without it. Other devices are logged out by Django, because
    their sessions were signed with the old password; the controller keeps this one.
    """
    user_id = ctx.actor.user_id
    if user_id is None:
        raise NotAuthenticated()
    ensure_within(f"change-password:user:{user_id}", PER_USER, now=ctx.now)
    user = users.get_user(user_id)
    if user.has_usable_password() and not user.check_password(current_password or ""):
        raise CurrentPasswordIncorrect()
    ensure_password_strong(new_password)
    users.set_password_hash(user_id, make_password(new_password), now=ctx.now)
