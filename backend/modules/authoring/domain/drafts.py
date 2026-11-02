"""A test as the authoring rules see it: settings, sections, questions, options
(domain_model.md §3.4). Drafts may be incomplete; `problems.py` says what's missing."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from core.rich_content import Json
from modules.authoring.domain.values import IntegrityAction, QuestionType, TimingKind


@dataclass(frozen=True, slots=True)
class Timing:
    kind: TimingKind
    # TOTAL only
    duration_s: int | None = None
    # PER_QUESTION only
    default_question_s: int | None = None
    # SECTIONED only: may students go back to an earlier section
    allow_return: bool = False


@dataclass(frozen=True, slots=True)
class Marking:
    marks: Decimal
    negative_marks: Decimal


@dataclass(frozen=True, slots=True)
class Integrity:
    grace_s: int
    max_warnings: int
    action: IntegrityAction


@dataclass(frozen=True, slots=True)
class TestSettings:
    timing: Timing
    shuffle_questions: bool
    shuffle_options: bool
    marking: Marking
    integrity: Integrity


@dataclass(frozen=True, slots=True)
class OptionDraft:
    id: UUID
    content: Json
    is_correct: bool


@dataclass(frozen=True, slots=True)
class QuestionDraft:
    id: UUID
    type: QuestionType
    stem: Json
    options: tuple[OptionDraft, ...] = ()
    numeric_answer: Decimal | None = None
    marks_override: Decimal | None = None
    negative_marks_override: Decimal | None = None
    time_override_s: int | None = None


@dataclass(frozen=True, slots=True)
class SectionDraft:
    id: UUID
    duration_s: int | None
    questions: tuple[QuestionDraft, ...]


@dataclass(frozen=True, slots=True)
class TestDraft:
    settings: TestSettings
    sections: tuple[SectionDraft, ...]

    def questions(self) -> list[QuestionDraft]:
        """Every question in paper order (section by section)."""
        return [question for section in self.sections for question in section.questions]
