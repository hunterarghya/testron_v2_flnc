"""Who may do what in delivery: ensure_<actor>_can_<action>(actor, obj) (R-07)."""

from uuid import UUID

from core.context import Actor
from core.errors import Forbidden


def ensure_active_student(actor: Actor) -> UUID:
    """Tests are sat by ACTIVE students only (security.md §3.1); returns their id. The router
    checks the area too; this second gate holds even if a route is ever mounted wrongly."""
    if not actor.is_active_student or actor.user_id is None:
        raise Forbidden()
    return actor.user_id
