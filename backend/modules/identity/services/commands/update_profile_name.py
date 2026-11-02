from core.context import Ctx
from core.errors import NotAuthenticated
from modules.identity.repositories import users


def update_profile_name(ctx: Ctx, *, name: str) -> None:
    """Change your own display name (P-11, T-19). `name` is already cleaned by the DTO."""
    if ctx.actor.user_id is None:
        raise NotAuthenticated()
    users.set_name(ctx.actor.user_id, name, now=ctx.now)
