from dataclasses import dataclass
from uuid import UUID

from core.context import Ctx
from core.errors import NotFound
from modules.assignments import public as assignments
from modules.delivery import public as delivery
from modules.grading import public as grading
from modules.results.domain.errors import ResultsNotPublished
from modules.results.policies import ensure_active_student
from modules.results.services.result_view import ResultView, Shown, result_view
from modules.results.services.standings import is_disqualified, is_visible, ranked


@dataclass(frozen=True, slots=True)
class MyResult:
    result: ResultView
    # A disqualified attempt shows "Disqualified", with no score, unless overridden (DM-5)
    score_hidden: bool


def get_my_result(ctx: Ctx, *, attempt_id: UUID) -> MyResult:
    """P-09 (domain_model.md §6.4): only once visible, and only what the publication options
    allow [H-2]. Someone else's attempt is not found; one not visible yet looks the same
    (results_not_published, a 404)."""
    student_id = ensure_active_student(ctx.actor)
    attempt = delivery.row_of(attempt_id)
    if attempt.student_id != student_id:
        raise NotFound("attempt")
    frame = assignments.get_results_frame_for_student(
        attempt.assignment_id, student_id, now=ctx.now
    )
    if not is_visible(frame, attempt, now=ctx.now):
        raise ResultsNotPublished()
    hidden = is_disqualified(attempt) and attempt.disqualification_overridden_at is None
    shown = Shown.by_options(frame.row.record.settings.publication)
    everyone = delivery.rows_of(attempt.assignment_id) if shown.rank and not hidden else []
    view = result_view(
        attempt,
        frame=frame,
        grades=grading.grades_of([attempt_id])[attempt_id],
        ranked=ranked(attempt, everyone),
        shown=Shown() if hidden else shown,
    )
    return MyResult(result=view, score_hidden=hidden)
