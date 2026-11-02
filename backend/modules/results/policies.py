"""Who may do what in results: ensure_<actor>_can_<action>(actor, obj) (R-07)."""

from core.context import Actor
from core.errors import Forbidden


def ensure_teacher(actor: Actor) -> None:
    """Gradebooks, publishing and the dashboard are the teacher's alone (security.md §3.1)."""
    if not actor.is_teacher:
        raise Forbidden()
