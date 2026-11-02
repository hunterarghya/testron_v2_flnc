from uuid import UUID

from core.context import Ctx
from modules.identity.repositories import sessions, users


def scrub_account(ctx: Ctx, *, user_id: UUID, name: str, email: str) -> None:
    """Replace the person's name and email with placeholders and remove every way to log in
    (password, Google link, sessions) (domain_model.md §3.2 #3). Results stay linked to the
    account id. Runs inside the caller's transaction.
    """
    users.scrub(user_id, name=name, email=email, now=ctx.now)
    sessions.delete_sessions_of(user_id)
