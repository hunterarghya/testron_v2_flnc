"""The whole attempt, on load and resume (api_contract.md §3.4 `AttemptState`): only the
questions the student may answer now, in their order. No correctness anywhere (rule 1)."""

from decimal import Decimal
from typing import Self
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict

from modules.delivery.domain.values import StageKind
from modules.delivery.dto.answers import AnswerOut, answer_out
from modules.delivery.dto.attempt_clock import AttemptClockOut
from modules.delivery.services.attempt_views import AttemptStateView, QuestionView, StageMeta

RichJson = dict[str, object]


class _Out(Schema):
    model_config = ConfigDict(extra="forbid")


class AttemptTimingOut(_Out):
    kind: str
    allow_return: bool


class AttemptIntegrityOut(_Out):
    grace_s: int
    max_warnings: int
    action: str


class StageMetaOut(_Out):
    index: int
    kind: StageKind
    title: str | None
    instructions: RichJson | None
    duration_s: int
    question_ids: list[UUID]

    @classmethod
    def from_meta(cls, meta: StageMeta) -> Self:
        stage = meta.stage
        return cls(
            index=stage.index,
            kind=stage.kind,
            title=meta.title,
            instructions=dict(meta.instructions) if meta.instructions else None,
            duration_s=stage.duration_s,
            question_ids=list(stage.question_ids),
        )


class HallOptionOut(_Out):
    id: UUID
    label: str
    content: RichJson


class HallQuestionOut(_Out):
    id: UUID
    number: int
    type: str
    stem: RichJson
    marks: Decimal
    negative_marks: Decimal
    time_s: int | None
    options: list[HallOptionOut]

    @classmethod
    def from_view(cls, view: QuestionView) -> Self:
        q = view.question
        return cls(
            id=q.id,
            number=view.number,
            type=q.type,
            stem=dict(q.stem),
            marks=q.marks,
            negative_marks=q.negative_marks,
            time_s=q.time_s,
            options=[
                HallOptionOut(id=o.id, label=o.label, content=dict(o.content)) for o in view.options
            ],
        )


class ResponseOut(_Out):
    answer: AnswerOut | None
    marked_for_review: bool
    visited: bool
    client_seq: int


class AttemptStateOut(AttemptClockOut):
    attempt_id: UUID
    assignment_id: UUID
    title: str
    take_number: int
    # Send it back as X-Exam-Client on every write, and keep it per attempt (§5.9)
    exam_client_id: UUID | None
    timing: AttemptTimingOut
    integrity: AttemptIntegrityOut
    stage_meta: list[StageMetaOut]
    questions: list[HallQuestionOut]
    # Keyed by question id (JSON object keys are strings)
    responses: dict[str, ResponseOut]

    @classmethod
    def from_state(cls, view: AttemptStateView) -> Self:
        attempt, paper = view.attempt, view.paper
        clock = AttemptClockOut.from_view(view.clock).model_dump()
        return cls(
            **clock,
            attempt_id=attempt.id,
            assignment_id=attempt.assignment_id,
            title=view.title,
            take_number=attempt.take_number,
            exam_client_id=attempt.active_client_id,
            timing=AttemptTimingOut(kind=paper.timing_kind, allow_return=paper.allow_return),
            integrity=AttemptIntegrityOut(
                grace_s=view.integrity.grace_s,
                max_warnings=view.integrity.max_warnings,
                action=view.integrity.action,
            ),
            stage_meta=[StageMetaOut.from_meta(m) for m in view.stage_meta],
            questions=[HallQuestionOut.from_view(q) for q in view.questions],
            responses={
                str(q): ResponseOut(
                    answer=answer_out(r.answer),
                    marked_for_review=r.marked_for_review,
                    visited=r.visited,
                    client_seq=r.client_seq,
                )
                for q, r in view.responses.items()
            },
        )
