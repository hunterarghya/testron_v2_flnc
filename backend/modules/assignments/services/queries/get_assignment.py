from uuid import UUID

from core.context import Ctx
from modules.assignments.policies import ensure_teacher
from modules.assignments.repositories import assignments
from modules.assignments.services.views import AssignmentDetail, assignment_detail


def get_assignment(ctx: Ctx, *, assignment_id: UUID) -> AssignmentDetail:
    """One assignment's overview (T-08): its settings, state, audience and what can still
    change (api_contract.md §3.3)."""
    ensure_teacher(ctx.actor)
    return assignment_detail(assignments.get_record(assignment_id), now=ctx.now)
