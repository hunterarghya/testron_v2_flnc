from collections.abc import Sequence
from uuid import UUID

from core.context import Ctx
from modules.identity.repositories import users


def set_accounts_active(ctx: Ctx, *, user_ids: Sequence[UUID], active: bool) -> None:
    """Keep Django's login flag equal to "the student is ACTIVE" (database_schema.md §5.3).
    Runs inside the caller's transaction."""
    users.set_active(user_ids, active=active, now=ctx.now)
