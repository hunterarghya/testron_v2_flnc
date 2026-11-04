"""The teacher's gradebook, question stats, answer key, inbox and dashboard (api_contract.md
§2.7, §2.2; T-01, T-11, T-13). The contract names these without fields; they are here
(ADR-079)."""

from collections.abc import Mapping
from decimal import Decimal
from typing import Self, cast
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict

from modules.assignments import public as assignments
from modules.results.dto.result import PartOut
from modules.results.services.queries.get_gradebook import Gradebook, GradebookRow
from modules.results.services.queries.get_question_stats import QuestionStatView

RichJson = dict[str, object]


class _Out(Schema):
    model_config = ConfigDict(extra="forbid")


class GradebookRowOut(_Out):
    student_id: UUID
    name: str
    attempt_id: UUID | None
    take_number: int | None
    # NOT_STARTED, ABSENT, IN_PROGRESS, or how it ended
    status: str
    rank: int | None
    score: Decimal | None
    max_score: Decimal | None
    sections: list[PartOut]
    time_taken_s: int | None
    warning_count: int
    overridden: bool

    @classmethod
    def from_row(cls, row: GradebookRow) -> Self:
        a = row.attempt
        return cls(
            student_id=row.student_id,
            name=row.name,
            attempt_id=a.id if a else None,
            take_number=a.take_number if a else None,
            status=row.status,
            rank=row.placing.rank if row.placing else None,
            score=a.score if a else None,
            max_score=a.max_score if a else None,
            sections=[PartOut(title=p.key, score=p.score, max=p.max) for p in row.sections],
            time_taken_s=row.time_taken_s,
            warning_count=a.warning_count if a else 0,
            overridden=bool(a and a.disqualification_overridden_at),
        )


class GradebookStatsOut(_Out):
    count: int
    mean: Decimal | None
    highest: Decimal | None
    lowest: Decimal | None
    attempted: int
    absent: int
    disqualified: int


class GradebookOut(_Out):
    title: str
    state: str
    publication_state: str
    rows: list[GradebookRowOut]
    stats: GradebookStatsOut

    @classmethod
    def from_book(cls, book: Gradebook) -> Self:
        s = book.stats
        return cls(
            title=book.frame.row.record.settings.title,
            state=book.frame.row.state.value,
            publication_state=book.frame.row.publication_state.value,
            rows=[GradebookRowOut.from_row(r) for r in book.rows],
            stats=GradebookStatsOut(
                count=s.count if s else 0,
                mean=s.mean if s else None,
                highest=s.highest if s else None,
                lowest=s.lowest if s else None,
                attempted=book.attempted,
                absent=book.absent,
                disqualified=book.disqualified,
            ),
        )


class TagRefOut(_Out):
    id: UUID
    name: str
    kind: str


class QuestionStatOut(_Out):
    question_id: UUID
    number: int
    type: str
    answered: int
    correct: int
    partial: int
    top_wrong_option_id: UUID | None
    top_wrong_count: int
    tags: list[TagRefOut]

    @classmethod
    def from_view(cls, view: QuestionStatView) -> Self:
        s = view.stat
        return cls(
            question_id=UUID(str(view.question["id"])),
            number=view.number,
            type=str(view.question["type"]),
            answered=s.answered,
            correct=s.correct,
            partial=s.partial,
            top_wrong_option_id=s.top_wrong_option,
            top_wrong_count=s.top_wrong_count,
            tags=[TagRefOut(id=t.id, name=t.name, kind=t.kind.value) for t in view.tags],
        )


class KeyedPaperOut(_Out):
    """The paper with its key and solutions (teacher only): the shapes of
    database_schema.md §4.2-4.3."""

    version: int
    paper: RichJson
    entries: RichJson
    solutions: RichJson

    @classmethod
    def from_keyed(cls, keyed: assignments.KeyedPaper) -> Self:
        entries = cast("Mapping[str, object]", keyed.entries["entries"])
        return cls(
            version=keyed.version,
            paper=dict(keyed.paper),
            entries=dict(entries),
            solutions=dict(keyed.solutions),
        )
