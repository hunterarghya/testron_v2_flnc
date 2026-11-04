"""A result (api_contract.md §3.5 `Result`, `AnswerSheet`): the student's P-09, filtered by
the publication options before it gets here, and the teacher's T-12 with everything."""

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Self, cast
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict

from modules.results.services.result_view import ResultQuestion, ResultView

RichJson = dict[str, object]
Json = Mapping[str, object]


class _Out(Schema):
    model_config = ConfigDict(extra="forbid")


class PartOut(_Out):
    title: str
    score: Decimal
    max: Decimal


class TagScoreOut(_Out):
    id: UUID
    name: str
    kind: str
    score: Decimal
    max: Decimal


class RankAndStatsOut(_Out):
    rank: int
    pool: int
    mean: Decimal
    highest: Decimal


class ResultOptionOut(_Out):
    id: UUID
    label: str
    content: RichJson


class CorrectAnswerOut(_Out):
    option_ids: list[UUID] | None = None
    value: Decimal | None = None
    tolerance: Decimal | None = None


class ResultQuestionOut(_Out):
    id: UUID
    number: int
    type: str
    stem: RichJson
    marks: Decimal
    negative_marks: Decimal
    options: list[ResultOptionOut]
    your_answer: RichJson | None = None
    correct_answer: CorrectAnswerOut | None = None
    outcome: str | None = None
    marks_awarded: Decimal | None = None
    solution: RichJson | None = None

    @classmethod
    def from_question(cls, item: ResultQuestion) -> Self:
        q = item.question
        options = {str(o["id"]): o for o in cast("Sequence[Json]", q.get("options", []))}
        order = [str(o) for o in item.option_order] or list(options)
        grade = item.grade
        return cls(
            id=UUID(str(q["id"])),
            number=item.number,
            type=str(q["type"]),
            stem=dict(cast("Json", q["stem"])),
            marks=Decimal(str(q["marks"])),
            negative_marks=Decimal(str(q["negative_marks"])),
            options=[
                ResultOptionOut(
                    id=UUID(o),
                    label=chr(ord("A") + i),
                    content=dict(cast("Json", options[o]["content"])),
                )
                for i, o in enumerate(order)
            ],
            your_answer=dict(item.your_answer) if item.your_answer else None,
            correct_answer=_correct(item.correct),
            outcome=grade.outcome.value if grade else None,
            marks_awarded=grade.marks_awarded if grade else None,
            solution=dict(item.solution) if item.solution else None,
        )


def _correct(entry: Json | None) -> CorrectAnswerOut | None:
    if entry is None:
        return None
    if entry["type"] == "NUMERICAL":
        return CorrectAnswerOut(
            value=Decimal(str(entry["answer"])), tolerance=Decimal(str(entry["tolerance"]))
        )
    return CorrectAnswerOut(
        option_ids=[UUID(o) for o in cast("list[str]", entry["correct_option_ids"])]
    )


class ResultOut(_Out):
    attempt_id: UUID
    label: str
    take_number: int
    ended_at: datetime | None
    time_taken_s: int
    end_reason: str | None
    # None for a disqualified attempt the teacher hasn't overridden (DM-5)
    score: Decimal | None
    max_score: Decimal
    sections: list[PartOut]
    tags: list[TagScoreOut]
    rank_and_stats: RankAndStatsOut | None
    questions: list[ResultQuestionOut] | None

    @classmethod
    def from_view(cls, view: ResultView, *, score_hidden: bool = False) -> Self:
        attempt = view.attempt
        return cls(
            attempt_id=attempt.id,
            label=view.label,
            take_number=attempt.take_number,
            ended_at=attempt.ended_at,
            time_taken_s=view.time_taken_s,
            end_reason=attempt.end_reason.value if attempt.end_reason else None,
            score=None if score_hidden else attempt.score,
            max_score=attempt.max_score,
            sections=[PartOut(title=p.key, score=p.score, max=p.max) for p in view.sections],
            tags=[
                TagScoreOut(
                    id=t.tag.id, name=t.tag.name, kind=t.tag.kind.value, score=t.score, max=t.max
                )
                for t in view.tags
            ],
            rank_and_stats=_rank(view),
            questions=[ResultQuestionOut.from_question(q) for q in view.questions]
            if view.questions is not None
            else None,
        )


def _rank(view: ResultView) -> RankAndStatsOut | None:
    if view.placing is None or view.stats is None:
        return None
    return RankAndStatsOut(
        rank=view.placing.rank,
        pool=view.placing.pool,
        mean=view.stats.mean,
        highest=view.stats.highest,
    )
