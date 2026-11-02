"""The whole test as the editor sees it (api_contract.md §3.2 TestDocument), and how the
rules (problems, totals) read it."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from core.rich_content import Json
from modules.authoring.domain.drafts import (
    OptionDraft,
    QuestionDraft,
    SectionDraft,
    TestDraft,
    TestSettings,
)
from modules.authoring.domain.effective import total_duration_s, total_marks
from modules.authoring.domain.problems import Problem, find_problems
from modules.authoring.domain.values import QuestionType


@dataclass(frozen=True, slots=True)
class TagLabel:
    id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class QuestionView:
    id: UUID
    section_id: UUID
    position: int
    type: QuestionType
    stem: Json
    solution: Json | None
    marks_override: Decimal | None
    negative_marks_override: Decimal | None
    time_override_s: int | None
    options: tuple[OptionDraft, ...]
    numeric_answer: Decimal | None
    numeric_tolerance: Decimal
    chapter_tags: tuple[TagLabel, ...]
    topic_tags: tuple[TagLabel, ...]

    def draft(self) -> QuestionDraft:
        return QuestionDraft(
            id=self.id,
            type=self.type,
            stem=self.stem,
            options=self.options,
            numeric_answer=self.numeric_answer,
            marks_override=self.marks_override,
            negative_marks_override=self.negative_marks_override,
            time_override_s=self.time_override_s,
        )


@dataclass(frozen=True, slots=True)
class SectionView:
    id: UUID
    position: int
    title: str
    instructions: Json | None
    duration_s: int | None
    questions: tuple[QuestionView, ...]


@dataclass(frozen=True, slots=True)
class Totals:
    questions: int
    marks: Decimal
    # None while some part of the test has no time yet
    duration_s: int | None


@dataclass(frozen=True, slots=True)
class TestDocumentView:
    id: UUID
    title: str
    instructions: Json | None
    settings: TestSettings
    revision: int
    archived_at: datetime | None
    last_assigned_at: datetime | None
    sections: tuple[SectionView, ...]

    def draft(self) -> TestDraft:
        sections = tuple(
            SectionDraft(s.id, s.duration_s, tuple(q.draft() for q in s.questions))
            for s in self.sections
        )
        return TestDraft(settings=self.settings, sections=sections)

    def problems(self) -> list[Problem]:
        return find_problems(self.draft())

    def totals(self) -> Totals:
        draft = self.draft()
        return Totals(len(draft.questions()), total_marks(draft), total_duration_s(draft))

    def question(self, question_id: UUID) -> QuestionView:
        return next(q for s in self.sections for q in s.questions if q.id == question_id)

    def section(self, section_id: UUID) -> SectionView:
        return next(s for s in self.sections if s.id == section_id)
