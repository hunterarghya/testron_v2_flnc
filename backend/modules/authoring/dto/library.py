"""The Test Library (T-02), question search and import (T-03 Import)."""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Self
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict, Field

from modules.authoring.domain.library import QuestionSearchRow, TestRow
from modules.authoring.dto.document import EditorQuestionOut, RichJson, TestMutationOut
from modules.authoring.dto.tags import TagOut
from modules.authoring.services.editing import EditResult


class _Schema(Schema):
    model_config = ConfigDict(extra="forbid")


class TestFilterIn(_Schema):
    q: str | None = Field(default=None, max_length=200)
    tag_id: UUID | None = None
    status: Literal["active", "archived"] = "active"
    sort: Literal["-updated_at", "title", "-last_assigned_at"] = "-updated_at"


class TestRowOut(_Schema):
    id: UUID
    title: str
    question_count: int
    total_marks: Decimal
    timing_kind: Literal["TOTAL", "PER_QUESTION", "SECTIONED"]
    problem_count: int
    last_assigned_at: datetime | None
    updated_at: datetime
    archived_at: datetime | None

    @classmethod
    def from_row(cls, row: TestRow) -> Self:
        return cls(
            id=row.id,
            title=row.title,
            question_count=row.question_count,
            total_marks=row.total_marks,
            timing_kind=row.timing_kind.value,
            problem_count=row.problem_count,
            last_assigned_at=row.last_assigned_at,
            updated_at=row.updated_at,
            archived_at=row.archived_at,
        )


class QuestionSearchIn(_Schema):
    q: str | None = Field(default=None, max_length=200)
    tag_id: UUID | None = None
    exclude_test_id: UUID | None = None


class QuestionSearchRowOut(_Schema):
    id: UUID
    test_id: UUID
    test_title: str
    type: Literal["MCQ", "MSQ", "NUMERICAL"]
    stem: RichJson
    chapter_tags: list[TagOut]
    topic_tags: list[TagOut]

    @classmethod
    def from_row(cls, row: QuestionSearchRow) -> Self:
        return cls(
            id=row.id,
            test_id=row.test_id,
            test_title=row.test_title,
            type=row.type.value,
            stem=row.stem,
            chapter_tags=[TagOut(id=t.id, kind="CHAPTER", name=t.name) for t in row.chapter_tags],
            topic_tags=[TagOut(id=t.id, kind="TOPIC", name=t.name) for t in row.topic_tags],
        )


class ImportIn(_Schema):
    revision: int
    source_question_ids: list[UUID] = Field(max_length=100)
    section_id: UUID
    after_question_id: UUID | None = None


class ImportOut(TestMutationOut):
    questions: list[EditorQuestionOut]

    @classmethod
    def with_questions(cls, result: EditResult[list[UUID]]) -> Self:
        base = TestMutationOut.from_result(result)
        imported = [
            EditorQuestionOut.from_view(result.document.question(qid)) for qid in result.made
        ]
        return cls(
            revision=base.revision, problems=base.problems, totals=base.totals, questions=imported
        )
