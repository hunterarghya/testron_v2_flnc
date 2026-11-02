"""Who may do what in media: ensure_<actor>_can_<action>(actor, obj) (R-07)."""

from core.context import Actor
from core.errors import Forbidden


def ensure_teacher_can_upload(actor: Actor) -> None:
    """Only the teacher adds images (to questions and the logo). The router checks the area
    too; this second gate holds even if a route is ever mounted wrongly."""
    if not actor.is_teacher:
        raise Forbidden()
