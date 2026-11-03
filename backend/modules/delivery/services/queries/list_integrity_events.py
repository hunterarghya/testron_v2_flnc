from uuid import UUID

from core.context import Ctx
from modules.delivery.policies import ensure_teacher
from modules.delivery.repositories import attempt_rows, integrity_events
from modules.delivery.repositories.integrity_events import EventRow


def list_integrity_events(ctx: Ctx, *, attempt_id: UUID) -> list[EventRow]:
    """T-10's ⚑ panel: each time the student left, when they came back, and whether it cost
    a warning; device changes are listed too (never counted, §5.9)."""
    ensure_teacher(ctx.actor)
    attempt_rows.row_of(attempt_id)
    return integrity_events.of_attempt(attempt_id)
