from uuid import UUID

from core.context import Ctx
from modules.identity.repositories import users


def mark_email_verified(ctx: Ctx, *, user_id: UUID) -> None:
    """Record that the user proved they own their email (once; later calls change nothing)."""
    users.mark_email_verified(user_id, now=ctx.now)
