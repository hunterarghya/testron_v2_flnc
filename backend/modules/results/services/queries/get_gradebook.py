from dataclasses import dataclass
from uuid import UUID

from core.context import Ctx
from modules.assignments import public as assignments
from modules.delivery import public as delivery
from modules.grading import public as grading
from modules.results.domain.breakdown import PartScore, section_scores, section_titles, time_taken_s
from modules.results.domain.ranking import Placing, Stats, placings, pool_stats
from modules.results.policies import ensure_teacher
from modules.results.services.standings import scored

ABSENT = "ABSENT"
NOT_STARTED = "NOT_STARTED"


@dataclass(frozen=True, slots=True)
class GradebookRow:
    student_id: UUID
    name: str
    # None: no attempt (absent once the test is closed, else not started)
    attempt: delivery.AttemptRow | None
    status: str
    placing: Placing | None
    sections: list[PartScore]
    time_taken_s: int | None


@dataclass(frozen=True, slots=True)
class Gradebook:
    frame: assignments.ResultsFrame
    rows: list[GradebookRow]
    # Over the first take's pool
    stats: Stats | None
    attempted: int
    absent: int
    disqualified: int


def get_gradebook(ctx: Ctx, *, assignment_id: UUID) -> Gradebook:
    """T-11 Students: every assigned student, absent ones included [H-4], one row per take
    [D-9], ranked on read (domain_model.md §6.3). Sittings whose time ran out end first. A
    fixed number of queries for any class size."""
    ensure_teacher(ctx.actor)
    members = delivery.finalize_assignment(ctx, assignment_id=assignment_id).members
    frame = assignments.get_results_frame(ctx, assignment_id=assignment_id)
    attempts = delivery.rows_of(assignment_id)
    grades = grading.grades_of([a.id for a in attempts if a.graded_at])
    ranks = placings(scored(attempts))
    titles = section_titles(frame.paper)
    closed = frame.row.state.value == "CLOSED"
    rows: list[GradebookRow] = []
    for member in members:
        mine = [a for a in attempts if a.student_id == member.student_id]
        rows += [
            _row(member.name, a, ranks.get(a.id), section_scores(grades.get(a.id, []), titles))
            for a in mine
        ]
        if not mine:
            rows.append(
                GradebookRow(
                    member.student_id,
                    member.name,
                    None,
                    ABSENT if closed else NOT_STARTED,
                    None,
                    [],
                    None,
                )
            )
    return Gradebook(
        frame=frame,
        rows=sorted(rows, key=_rank_order),
        stats=pool_stats(scored(attempts)),
        attempted=len({a.student_id for a in attempts}),
        absent=sum(row.status == ABSENT for row in rows),
        disqualified=sum(row.status == "DISQUALIFIED" for row in rows),
    )


def _row(
    name: str, attempt: delivery.AttemptRow, placing: Placing | None, sections: list[PartScore]
) -> GradebookRow:
    status = attempt.end_reason.value if attempt.end_reason else attempt.status.value
    return GradebookRow(
        student_id=attempt.student_id,
        name=name,
        attempt=attempt,
        status=status,
        placing=placing,
        sections=sections,
        time_taken_s=time_taken_s(attempt.started_at, attempt.ended_at)
        if attempt.ended_at
        else None,
    )


def _rank_order(row: GradebookRow) -> tuple[bool, int, int, str]:
    """Ranked first (by take, then rank), then the rest by name."""
    take = row.attempt.take_number if row.attempt else 99
    return (row.placing is None, take, row.placing.rank if row.placing else 0, row.name.casefold())
