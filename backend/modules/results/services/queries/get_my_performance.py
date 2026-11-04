from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery import public as delivery
from modules.results.domain.errors import PerformanceNotShared
from modules.results.policies import ensure_active_student
from modules.results.services.performance_view import PerformanceView, performance_of
from modules.results.services.standings import counts, is_visible
from modules.students import public as students


def get_my_performance(ctx: Ctx) -> PerformanceView:
    """P-10 (domain_model.md §6.5): only while the teacher shares it [I-3], and only from
    results the student can already see [I-4], so nothing leaks before publication."""
    student_id = ensure_active_student(ctx.actor)
    if not students.is_performance_shared(student_id):
        raise PerformanceNotShared()
    delivery.finalize_student(ctx, student_id=student_id)
    frames = {
        f.row.record.id: f
        for f in assignments.list_results_frames_for_student(student_id, now=ctx.now)
    }
    visible = [
        a
        for a in delivery.rows_of_student(student_id)
        if counts(a)
        and a.assignment_id in frames
        and is_visible(frames[a.assignment_id], a, now=ctx.now)
    ]
    return performance_of(visible)
