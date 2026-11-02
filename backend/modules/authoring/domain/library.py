"""What the Test Library and the Import picker show per row (T-02, T-03 Import)."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from core.rich_content import Json
from modules.authoring.domain.document import TagLabel, TestDocumentView
from modules.authoring.domain.values import QuestionType, TimingKind


class LibrarySort(StrEnum):
    EDITED = "-updated_at"
    TITLE = "title"
    LAST_USED = "-last_assigned_at"


@dataclass(frozen=True, slots=True)
class TestFilter:
    """What the library shows: active or archived tests, found by text (title or the tags on
    their questions) or by one tag, in one order."""

    archived: bool = False
    search: str | None = None
    tag_id: UUID | None = None
    sort: LibrarySort = LibrarySort.EDITED


@dataclass(frozen=True, slots=True)
class TestRow:
    id: UUID
    title: str
    question_count: int
    total_marks: Decimal
    timing_kind: TimingKind
    # The `⚠ n` badge: a test with problems can't be assigned
    problem_count: int
    last_assigned_at: datetime | None
    updated_at: datetime
    archived_at: datetime | None


def row_of(document: TestDocumentView) -> TestRow:
    totals = document.totals()
    return TestRow(
        id=document.id,
        title=document.title,
        question_count=totals.questions,
        total_marks=totals.marks,
        timing_kind=document.settings.timing.kind,
        problem_count=len(document.problems()),
        last_assigned_at=document.last_assigned_at,
        updated_at=document.updated_at,
        archived_at=document.archived_at,
    )


@dataclass(frozen=True, slots=True)
class QuestionSearchRow:
    id: UUID
    test_id: UUID
    test_title: str
    type: QuestionType
    stem: Json
    chapter_tags: tuple[TagLabel, ...]
    topic_tags: tuple[TagLabel, ...]
