"""What the editor reads: TestDocument, EditorQuestion and TestMutation (api_contract.md §3.2).
Marks are decimal strings; rich content is the stored, normalized JSON."""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Self
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict

from modules.authoring.domain.document import (
    QuestionView,
    SectionView,
    TagLabel,
    TestDocumentView,
    Totals,
)
from modules.authoring.domain.problems import Problem
from modules.authoring.dto.document_settings import TestSettingsOut
from modules.authoring.dto.tags import TagOut
from modules.authoring.services.editing import EditResult

RichJson = dict[str, object]


class _Out(Schema):
    model_config = ConfigDict(extra="forbid")


class OptionOut(_Out):
    id: UUID
    content: RichJson
    is_correct: bool


class EditorQuestionOut(_Out):
    id: UUID
    section_id: UUID
    position: int
    type: Literal["MCQ", "MSQ", "NUMERICAL"]
    stem: RichJson
    solution: RichJson | None
    marks_override: Decimal | None
    negative_marks_override: Decimal | None
    time_override_s: int | None
    options: list[OptionOut]
    numeric_answer: Decimal | None
    numeric_tolerance: Decimal
    chapter_tags: list[TagOut]
    topic_tags: list[TagOut]

    @classmethod
    def from_view(cls, q: QuestionView) -> Self:
        return cls(
            id=q.id,
            section_id=q.section_id,
            position=q.position,
            type=q.type.value,
            stem=q.stem,
            solution=q.solution,
            marks_override=q.marks_override,
            negative_marks_override=q.negative_marks_override,
            time_override_s=q.time_override_s,
            options=[
                OptionOut(id=o.id, content=o.content, is_correct=o.is_correct) for o in q.options
            ],
            numeric_answer=q.numeric_answer,
            numeric_tolerance=q.numeric_tolerance,
            chapter_tags=_tags(q.chapter_tags, "CHAPTER"),
            topic_tags=_tags(q.topic_tags, "TOPIC"),
        )


def _tags(labels: tuple[TagLabel, ...], kind: Literal["CHAPTER", "TOPIC"]) -> list[TagOut]:
    return [TagOut(id=label.id, kind=kind, name=label.name) for label in labels]


class SectionOut(_Out):
    id: UUID
    position: int
    title: str
    instructions: RichJson | None
    duration_s: int | None
    questions: list[EditorQuestionOut]

    @classmethod
    def from_view(cls, s: SectionView) -> Self:
        questions = [EditorQuestionOut.from_view(q) for q in s.questions]
        return cls(
            id=s.id,
            position=s.position,
            title=s.title,
            instructions=s.instructions,
            duration_s=s.duration_s,
            questions=questions,
        )


class TotalsOut(_Out):
    questions: int
    marks: Decimal
    duration_s: int | None

    @classmethod
    def from_totals(cls, totals: Totals) -> Self:
        return cls(questions=totals.questions, marks=totals.marks, duration_s=totals.duration_s)


class ProblemOut(_Out):
    code: str
    message: str
    section_id: UUID | None
    question_id: UUID | None

    @classmethod
    def from_problem(cls, p: Problem) -> Self:
        return cls(
            code=p.code, message=p.message, section_id=p.section_id, question_id=p.question_id
        )


class TestDocumentOut(_Out):
    id: UUID
    title: str
    instructions: RichJson | None
    settings: TestSettingsOut
    revision: int
    archived_at: datetime | None
    last_assigned_at: datetime | None
    totals: TotalsOut
    sections: list[SectionOut]
    problems: list[ProblemOut]

    @classmethod
    def from_view(cls, d: TestDocumentView) -> Self:
        return cls(
            id=d.id,
            title=d.title,
            instructions=d.instructions,
            settings=TestSettingsOut.from_settings(d.settings),
            revision=d.revision,
            archived_at=d.archived_at,
            last_assigned_at=d.last_assigned_at,
            totals=TotalsOut.from_totals(d.totals()),
            sections=[SectionOut.from_view(s) for s in d.sections],
            problems=[ProblemOut.from_problem(p) for p in d.problems()],
        )


class TestMutationOut(_Out):
    revision: int
    problems: list[ProblemOut]
    totals: TotalsOut

    @classmethod
    def from_result(cls, result: EditResult[object]) -> Self:
        return cls(
            revision=result.revision,
            problems=[ProblemOut.from_problem(p) for p in result.problems],
            totals=TotalsOut.from_totals(result.totals),
        )


class SectionMutationOut(TestMutationOut):
    section: SectionOut

    @classmethod
    def with_section(cls, result: EditResult[UUID]) -> Self:
        base = TestMutationOut.from_result(result)
        section = SectionOut.from_view(result.document.section(result.made))
        return cls(
            revision=base.revision, problems=base.problems, totals=base.totals, section=section
        )


class QuestionMutationOut(TestMutationOut):
    question: EditorQuestionOut

    @classmethod
    def with_question(cls, result: EditResult[UUID]) -> Self:
        base = TestMutationOut.from_result(result)
        question = EditorQuestionOut.from_view(result.document.question(result.made))
        return cls(
            revision=base.revision, problems=base.problems, totals=base.totals, question=question
        )
