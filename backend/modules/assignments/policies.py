"""Who may do what in assignments: ensure_<actor>_can_<action>(actor, obj) (R-07)."""

from core.context import Actor
from core.errors import Forbidden


def ensure_teacher(actor: Actor) -> None:
    """Assignments are managed by the teacher alone (security.md §3.1). The router checks the
    area too; this second gate holds even if a route is ever mounted wrongly."""
    if not actor.is_teacher:
        raise Forbidden()
