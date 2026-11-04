"""Who may do what in results: ensure_<actor>_can_<action>(actor, obj) (R-07)."""

from uuid import UUID

from core.context import Actor
from core.errors import Forbidden


def ensure_teacher(actor: Actor) -> None:
    """Gradebooks, publishing and the dashboard are the teacher's alone (security.md §3.1)."""
    if not actor.is_teacher:
        raise Forbidden()


def ensure_active_student(actor: Actor) -> UUID:
    """Past Tests and results are the student's own (security.md §3.1); returns their id."""
    if not actor.is_active_student or actor.user_id is None:
        raise Forbidden()
    return actor.user_id
