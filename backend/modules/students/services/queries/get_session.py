from dataclasses import dataclass
from datetime import datetime

from core.context import Ctx
from modules.students.services.session_user import SessionUserView, build_session_user


@dataclass(frozen=True, slots=True)
class SessionView:
    user: SessionUserView | None
    server_now: datetime


def get_session(ctx: Ctx) -> SessionView:
    """Who is logged in, if anyone, and the server time (api_contract.md §2.1, SPA boot).

    Anyone may ask; a visitor gets `user: null`. The SPA routes by role and status from
    this answer (screens.md S-01).
    """
    user_id = ctx.actor.user_id
    user = build_session_user(user_id) if user_id is not None else None
    return SessionView(user=user, server_now=ctx.now)
