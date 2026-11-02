"""Who may do what in authoring: ensure_<actor>_can_<action>(actor, obj) (R-07)."""

from core.context import Actor
from core.errors import Forbidden


def ensure_teacher(actor: Actor) -> None:
    """Tests, questions and tags are the teacher's alone (security.md §3.1). The router checks
    the area too; this second gate holds even if a route is ever mounted wrongly."""
    if not actor.is_teacher:
        raise Forbidden()
