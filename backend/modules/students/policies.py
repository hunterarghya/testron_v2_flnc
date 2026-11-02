"""Who may do what in students: ensure_<actor>_can_<action>(actor, obj) (R-07)."""

from core.context import Actor
from core.errors import Forbidden


def ensure_teacher(actor: Actor) -> None:
    """Admission and groups are the teacher's alone (security.md §3.1). The router already
    checks the area; this second gate holds even if a route is ever mounted wrongly."""
    if not actor.is_teacher:
        raise Forbidden()
