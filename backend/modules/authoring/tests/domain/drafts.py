"""Builders for authoring drafts in domain tests."""

from dataclasses import replace
from decimal import Decimal
from uuid import UUID, uuid4

from core.rich_content import EMPTY_DOC, Json
from modules.authoring.domain.drafts import (
    Integrity,
    Marking,
    OptionDraft,
    QuestionDraft,
    SectionDraft,
    TestDraft,
    TestSettings,
    Timing,
)
from modules.authoring.domain.values import IntegrityAction, QuestionType, TimingKind


def words(value: str) -> Json:
    return {
        "v": 1,
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": value}]}],
    }


def settings(timing: Timing | None = None, **marking: Decimal) -> TestSettings:
    return TestSettings(
        timing=timing or Timing(TimingKind.TOTAL, duration_s=3600),
        shuffle_questions=False,
        shuffle_options=False,
        marking=Marking(
            marks=marking.get("marks", Decimal(4)),
            negative_marks=marking.get("negative", Decimal(1)),
        ),
        integrity=Integrity(grace_s=5, max_warnings=3, action=IntegrityAction.AUTO_SUBMIT),
    )


def option(text: str = "Mitochondria", *, correct: bool = False) -> OptionDraft:
    return OptionDraft(id=uuid4(), content=words(text) if text else EMPTY_DOC, is_correct=correct)


def mcq(**changes: object) -> QuestionDraft:
    question = QuestionDraft(
        id=uuid4(),
        type=QuestionType.MCQ,
        stem=words("Which organelle makes energy?"),
        options=(option(correct=True), option("Golgi body")),
    )
    return replace(question, **changes)  # type: ignore[arg-type]  # test builders pass fields


def section(
    *questions: QuestionDraft, duration_s: int | None = None, section_id: UUID | None = None
) -> SectionDraft:
    return SectionDraft(id=section_id or uuid4(), duration_s=duration_s, questions=questions)


def draft_of(*sections: SectionDraft, timing: Timing | None = None) -> TestDraft:
    return TestDraft(settings=settings(timing), sections=sections)
