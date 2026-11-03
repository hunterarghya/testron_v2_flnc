from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery.policies import ensure_active_student
from modules.delivery.services.commands.finalize_expired import finalize_expired
from modules.delivery.services.gate_views import GateView, gate_view


def get_gate_state(ctx: Ctx, *, assignment_id: UUID) -> GateView:
    """P-02, polled every 5 s while waiting: the rules, whether the student may begin, and
    why not. It is also the lobby heartbeat: each poll marks the student "Joined" for the
    teacher (T-09). Someone outside the audience gets not found (A-02)."""
    student_id = ensure_active_student(ctx.actor)
    with transaction.atomic():
        mine = assignments.get_student_assignment(assignment_id, student_id)
        assignments.touch_lobby_presence(assignment_id, student_id, now=ctx.now)
    sittings = finalize_expired(ctx, student_id, [mine])[assignment_id]
    return gate_view(mine, sittings, now=ctx.now)
