from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from core.context import Ctx
from core.rich_content import Json
from modules.assignments.domain.assignment import AssignmentRecord
from modules.assignments.policies import ensure_teacher
from modules.assignments.repositories import assignments, papers
from modules.assignments.services.views import AssignmentRow, assignment_rows


@dataclass(frozen=True, slots=True)
class ResultsFrame:
    """The assignment's side of a result (T-11, P-08, P-09): its state, when it ends for
    everyone, its publication settings and the frozen paper (never the key)."""

    row: AssignmentRow
    paper: Json


@dataclass(frozen=True, slots=True)
class KeyedPaper:
    """The paper with its answers (T-11 answer key, D-05): for the teacher, or for a student's
    result under answer review."""

    paper: Json
    entries: Json
    solutions: Json
    version: int


def get_results_frame(ctx: Ctx, *, assignment_id: UUID) -> ResultsFrame:
    ensure_teacher(ctx.actor)
    return _frames([assignments.get_record(assignment_id)], now=ctx.now)[0]


def list_results_frames_for_student(student_id: UUID, *, now: datetime) -> list[ResultsFrame]:
    """Every assignment the student is in, not cancelled. No policy: the caller is results'
    student use case, which checks the student first."""
    return _frames(assignments.list_records_for_student(student_id), now=now)


def get_results_frame_for_student(
    assignment_id: UUID, student_id: UUID, *, now: datetime
) -> ResultsFrame:
    """One the student is in; otherwise not found. No policy: the caller checks the student."""
    return _frames([assignments.get_record_for_student(assignment_id, student_id)], now=now)[0]


def get_keyed_paper(assignment_id: UUID) -> KeyedPaper:
    """No policy: results decides who may see answers (the teacher, or a visible result)."""
    version, entries = papers.answer_key(assignment_id)
    paper = papers.contents([assignment_id])[assignment_id]
    return KeyedPaper(paper, entries, papers.solutions(assignment_id), version)


def _frames(records: list[AssignmentRecord], *, now: datetime) -> list[ResultsFrame]:
    rows = assignment_rows(records, now=now)
    contents = papers.contents([row.record.id for row in rows])
    return [ResultsFrame(row, contents[row.record.id]) for row in rows]
