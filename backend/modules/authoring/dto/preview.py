"""The teacher's preview of a test (T-05): the student's paper, plus answers on request."""

from decimal import Decimal
from typing import Literal, Self
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict

from modules.authoring.domain.preview import PreviewPaper
from modules.authoring.dto.document import RichJson
from modules.authoring.dto.document_settings import Integrity


class _Schema(Schema):
    model_config = ConfigDict(extra="forbid")


class PreviewIn(_Schema):
    show_answers: bool = False


class PreviewTimingOut(_Schema):
    kind: Literal["TOTAL", "PER_QUESTION", "SECTIONED"]
    allow_return: bool


class PreviewOptionOut(_Schema):
    id: UUID
    label: str
    content: RichJson


class PreviewQuestionOut(_Schema):
    id: UUID
    number: int
    type: Literal["MCQ", "MSQ", "NUMERICAL"]
    stem: RichJson
    marks: Decimal
    negative_marks: Decimal
    time_s: int | None
    options: list[PreviewOptionOut]


class PreviewStageOut(_Schema):
    index: int
    kind: Literal["WHOLE", "SECTION", "QUESTION"]
    title: str | None
    instructions: RichJson | None
    duration_s: int | None
    question_ids: list[UUID]


class PreviewAnswerOut(_Schema):
    question_id: UUID
    correct_option_ids: list[UUID]
    numeric_answer: Decimal | None
    numeric_tolerance: Decimal
    solution: RichJson | None


class PreviewOut(_Schema):
    test_id: UUID
    title: str
    instructions: RichJson | None
    timing: PreviewTimingOut
    integrity: Integrity
    stages: list[PreviewStageOut]
    questions: list[PreviewQuestionOut]
    answers: list[PreviewAnswerOut]

    @classmethod
    def from_paper(cls, paper: PreviewPaper) -> Self:
        return cls.model_validate(
            {
                "test_id": paper.test_id,
                "title": paper.title,
                "instructions": paper.instructions,
                "timing": {"kind": paper.timing_kind.value, "allow_return": paper.allow_return},
                "integrity": {
                    "grace_s": paper.integrity.grace_s,
                    "max_warnings": paper.integrity.max_warnings,
                    "action": paper.integrity.action.value,
                },
                "stages": paper.stages,
                "questions": paper.questions,
                "answers": paper.answers,
            },
            from_attributes=True,
        )
