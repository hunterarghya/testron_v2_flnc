from uuid import UUID

from core.context import Ctx
from core.errors import NotFound
from modules.delivery import public as delivery
from modules.results.policies import ensure_teacher
from modules.results.services.performance_view import PerformanceView, performance_of
from modules.results.services.standings import counts
from modules.students import public as students


def get_student_performance(ctx: Ctx, *, student_id: UUID) -> PerformanceView:
    """T-15's performance tab (domain_model.md §6.5): every counted attempt, published or
    not, because the teacher sees everything. Sittings whose time ran out end first."""
    ensure_teacher(ctx.actor)
    if not students.describe_students([student_id]):
        raise NotFound("student")
    delivery.finalize_student(ctx, student_id=student_id)
    return performance_of([a for a in delivery.rows_of_student(student_id) if counts(a)])
