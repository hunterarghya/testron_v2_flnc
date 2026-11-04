from uuid import UUID

from core.context import Ctx
from modules.assignments import public as assignments
from modules.results.policies import ensure_teacher


def get_answer_key_view(ctx: Ctx, *, assignment_id: UUID) -> assignments.KeyedPaper:
    """T-11's answer key and D-05: the paper with the current key and solutions. Teacher only:
    no student response ever carries it (rule 1)."""
    ensure_teacher(ctx.actor)
    return assignments.get_keyed_paper(assignment_id)
