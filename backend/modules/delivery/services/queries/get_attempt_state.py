from uuid import UUID

from core.context import Ctx
from modules.delivery.policies import ensure_active_student
from modules.delivery.services.attempt_views import AttemptStateView
from modules.delivery.services.opening import open_attempt


def get_attempt_state(ctx: Ctx, *, attempt_id: UUID, client_id: UUID | None) -> AttemptStateView:
    """P-03 load and resume (E-02): the clock, the open stage's questions in the student's
    order and every saved answer, rebuilt from the server. Opening it on another device takes
    over (§5.9). Someone else's attempt is not found (A-03)."""
    student_id = ensure_active_student(ctx.actor)
    return open_attempt(ctx, attempt_id, student_id, client_id=client_id)
