"""The student's view of a test, for the teacher's preview (T-05): stages as the exam hall
runs them (domain_model.md §5.1), questions numbered, options lettered, marks resolved.
Nothing is shuffled; answers and solutions only when asked for."""

from dataclasses import dataclass
from decimal import Decimal
from string import ascii_uppercase
from uuid import UUID

from core.rich_content import Json
from modules.authoring.domain.document import QuestionView, TestDocumentView
from modules.authoring.domain.drafts import Integrity, TestSettings
from modules.authoring.domain.effective import (
    effective_marks,
    effective_negative_marks,
    effective_time_s,
)
from modules.authoring.domain.values import QuestionType, TimingKind


@dataclass(frozen=True, slots=True)
class PreviewOption:
    id: UUID
    label: str
    content: Json


@dataclass(frozen=True, slots=True)
class PreviewQuestion:
    id: UUID
    number: int
    type: QuestionType
    stem: Json
    marks: Decimal
    negative_marks: Decimal
    time_s: int | None
    options: tuple[PreviewOption, ...]


@dataclass(frozen=True, slots=True)
class PreviewStage:
    index: int
    # WHOLE (total timer), SECTION (sectioned) or QUESTION (per question)
    kind: str
    title: str | None
    instructions: Json | None
    # None while the teacher hasn't set it yet
    duration_s: int | None
    question_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class PreviewAnswer:
    question_id: UUID
    correct_option_ids: tuple[UUID, ...]
    numeric_answer: Decimal | None
    numeric_tolerance: Decimal
    solution: Json | None


@dataclass(frozen=True, slots=True)
class PreviewPaper:
    test_id: UUID
    title: str
    instructions: Json | None
    timing_kind: TimingKind
    allow_return: bool
    integrity: Integrity
    stages: tuple[PreviewStage, ...]
    questions: tuple[PreviewQuestion, ...]
    # Empty unless the teacher asked to see them
    answers: tuple[PreviewAnswer, ...]


def preview_paper(document: TestDocumentView, *, show_answers: bool) -> PreviewPaper:
    settings = document.settings
    ordered = [q for section in document.sections for q in section.questions]
    questions = tuple(_question(q, number, settings) for number, q in enumerate(ordered, start=1))
    return PreviewPaper(
        test_id=document.id,
        title=document.title,
        instructions=document.instructions,
        timing_kind=settings.timing.kind,
        allow_return=settings.timing.allow_return,
        integrity=settings.integrity,
        stages=_stages(document),
        questions=questions,
        answers=tuple(_answer(q) for q in ordered) if show_answers else (),
    )


def _question(question: QuestionView, number: int, settings: TestSettings) -> PreviewQuestion:
    draft = question.draft()
    options = tuple(
        PreviewOption(option.id, ascii_uppercase[index], option.content)
        for index, option in enumerate(question.options)
    )
    return PreviewQuestion(
        id=question.id,
        number=number,
        type=question.type,
        stem=question.stem,
        marks=effective_marks(draft, settings),
        negative_marks=effective_negative_marks(draft, settings),
        time_s=effective_time_s(draft, settings),
        options=options,
    )


def _stages(document: TestDocumentView) -> tuple[PreviewStage, ...]:
    settings = document.settings
    kind = settings.timing.kind
    if kind is TimingKind.SECTIONED:
        return tuple(
            PreviewStage(
                i,
                "SECTION",
                s.title or None,
                s.instructions,
                s.duration_s,
                tuple(q.id for q in s.questions),
            )
            for i, s in enumerate(document.sections)
        )
    ordered = [q for section in document.sections for q in section.questions]
    if kind is TimingKind.PER_QUESTION:
        return tuple(
            PreviewStage(i, "QUESTION", None, None, effective_time_s(q.draft(), settings), (q.id,))
            for i, q in enumerate(ordered)
        )
    return (
        PreviewStage(
            0, "WHOLE", None, None, settings.timing.duration_s, tuple(q.id for q in ordered)
        ),
    )


def _answer(question: QuestionView) -> PreviewAnswer:
    return PreviewAnswer(
        question_id=question.id,
        correct_option_ids=tuple(option.id for option in question.options if option.is_correct),
        numeric_answer=question.numeric_answer,
        numeric_tolerance=question.numeric_tolerance,
        solution=question.solution,
    )
