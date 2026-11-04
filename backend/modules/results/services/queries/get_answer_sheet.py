from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery import public as delivery
from modules.grading import public as grading
from modules.results.policies import ensure_teacher
from modules.results.services.result_view import ResultView, Shown, result_view
from modules.results.services.standings import ranked
from modules.students import public as students


@dataclass(frozen=True, slots=True)
class SheetFlags:
    """T-12's flags panel: the warnings against the test's limit, and whether the teacher
    counted a disqualified attempt anyway, and why (D-09)."""

    warning_count: int
    max_warnings: int
    # What the last warning did: AUTO_SUBMIT or DISQUALIFY
    action: str
    overridden_at: datetime | None
    override_reason: str | None


@dataclass(frozen=True, slots=True)
class AnswerSheet:
    """T-12: the result with everything, whoever sees what (domain_model.md §6.4)."""

    result: ResultView
    student_name: str
    events: list[delivery.EventRow]
    flags: SheetFlags


def get_answer_sheet(ctx: Ctx, *, attempt_id: UUID) -> AnswerSheet:
    ensure_teacher(ctx.actor)
    attempt = delivery.row_of(attempt_id)
    return list_answer_sheets(ctx, assignment_id=attempt.assignment_id, attempt_ids=[attempt_id])[0]


def list_answer_sheets(
    ctx: Ctx, *, assignment_id: UUID, attempt_ids: list[UUID] | None
) -> list[AnswerSheet]:
    """T-11 Export: the sheets of the chosen ended attempts (all when none are chosen), for the
    browser to turn into files (ADR-019). Not for the hall: it reads per attempt."""
    ensure_teacher(ctx.actor)
    frame = assignments.get_results_frame(ctx, assignment_id=assignment_id)
    everyone = delivery.rows_of(assignment_id)
    chosen = [a for a in everyone if a.ended_at and (attempt_ids is None or a.id in attempt_ids)]
    grades = grading.grades_of([a.id for a in chosen])
    names = {
        s.student_id: s.name for s in students.describe_students([a.student_id for a in chosen])
    }
    return [
        AnswerSheet(
            result=result_view(
                a,
                frame=frame,
                grades=grades[a.id],
                ranked=ranked(a, everyone),
                shown=Shown.everything(),
            ),
            student_name=names.get(a.student_id, ""),
            events=delivery.integrity_events_of(a.id),
            flags=_flags(a, frame),
        )
        for a in chosen
    ]


def _flags(attempt: delivery.AttemptRow, frame: assignments.ResultsFrame) -> SheetFlags:
    integrity = frame.row.record.settings.integrity
    overridden = attempt.disqualification_overridden_at
    return SheetFlags(
        warning_count=attempt.warning_count,
        max_warnings=integrity.max_warnings,
        action=integrity.action,
        overridden_at=overridden,
        # Only overridden attempts cost the audit-log read
        override_reason=delivery.get_override_reason(attempt.id) if overridden else None,
    )


def disqualified_score(sheet: AnswerSheet) -> Decimal | None:
    """The score in brackets beside "Disqualified" (T-11, G-2)."""
    attempt = sheet.result.attempt
    reason = attempt.end_reason.value if attempt.end_reason else None
    return attempt.score if reason == "DISQUALIFIED" else None
