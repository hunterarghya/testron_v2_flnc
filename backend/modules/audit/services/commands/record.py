from collections.abc import Mapping
from uuid import UUID

from core.context import Ctx
from modules.audit.repositories import entries


def record(
    ctx: Ctx,
    *,
    action: str,
    target_type: str,
    target_id: UUID,
    data: Mapping[str, object] | None = None,
) -> None:
    """Note a sensitive action, by whom and when, in the caller's transaction (security.md T-06).
    No policy: callers have already checked who may do it."""
    entries.insert_entry(
        actor_id=ctx.actor.user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        data=data or {},
        at=ctx.now,
    )
