"""Tests, sections and questions for tests that need some content (not the use cases' rules)."""

from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

from modules.authoring.models import Option, Question, QuestionTag, Section, Test

EMPTY = {"v": 1, "type": "doc", "content": []}


def doc_with(text: str) -> dict[str, object]:
    return {
        "v": 1,
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
    }


def make_test(**fields: object) -> Test:
    values: dict[str, object] = {
        "title": "Cell Biology",
        "timing_kind": "TOTAL",
        "duration_s": 3600,
        "marks": Decimal(4),
        "negative_marks": Decimal(1),
        "integrity_grace_s": 5,
        "integrity_max_warnings": 3,
        "integrity_action": "AUTO_SUBMIT",
    }
    return Test.objects.create(**(values | fields))


def make_section(test: Test, position: int = 0, **fields: object) -> Section:
    return Section.objects.create(test=test, position=position, **fields)


def make_question(
    section: Section,
    position: int = 0,
    *,
    text: str = "Which organelle makes energy?",
    tag_ids: Sequence[UUID] = (),
    options: int = 4,
) -> Question:
    question = Question.objects.create(
        test_id=section.test_id,
        section=section,
        position=position,
        type="MCQ",
        stem=doc_with(text),
        search_text=text,
    )
    Option.objects.bulk_create(
        [
            Option(
                question=question,
                position=i,
                content=doc_with(f"Option {i + 1}"),
                is_correct=i == 0,
            )
            for i in range(options)
        ]
    )
    QuestionTag.objects.bulk_create([QuestionTag(question=question, tag_id=tag) for tag in tag_ids])
    return question
