from core.context import Ctx
from core.errors import NotAuthenticated
from modules.identity import public as identity
from modules.students.services.session_user import SessionUserView, build_session_user


def update_profile_name(ctx: Ctx, *, name: str) -> SessionUserView:
    """Change your own name and get the updated SessionUser back (P-11, T-19)."""
    if ctx.actor.user_id is None:
        raise NotAuthenticated()
    identity.update_profile_name(ctx, name=name)
    return build_session_user(ctx.actor.user_id)
