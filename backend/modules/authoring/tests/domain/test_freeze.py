"""Freezing a test (domain_model.md §4.3): resolved settings, timing override, and a paper
that holds no answers by construction (V1 F-03)."""

import json
from dataclasses import replace
from decimal import Decimal
from uuid import uuid4

import pytest

from core.errors import FieldsInvalid
from modules.authoring.domain.document import QuestionView, SectionView, TagLabel, TestDocumentView
from modules.authoring.domain.drafts import OptionDraft, Timing
from modules.authoring.domain.errors import TestHasProblems
from modules.authoring.domain.freeze import TimingOverride, freeze, paper_questions
from modules.authoring.domain.values import QuestionType, TimingKind
from modules.authoring.tests.domain.drafts import settings, words

ANSWER_WORDS = (
    "is_correct",
    "numeric_answer",
    "tolerance",
    "solution",
    "correct_option_ids",
    "answer",
)


def question(kind: QuestionType = QuestionType.MCQ, **changes: object) -> QuestionView:
    view = QuestionView(
        id=uuid4(),
        section_id=uuid4(),
        position=0,
        type=kind,
        stem=words("Which organelle?"),
        solution=words("The mitochondrion"),
        marks_override=None,
        negative_marks_override=None,
        time_override_s=None,
        options=(
            OptionDraft(uuid4(), words("Mitochondria"), True),
            OptionDraft(uuid4(), words("Golgi"), False),
        ),
        numeric_answer=None,
        numeric_tolerance=Decimal(0),
        chapter_tags=(TagLabel(uuid4(), "Cell"),),
        topic_tags=(),
    )
    return replace(view, **changes)  # type: ignore[arg-type]


def document(
    *questions: QuestionView, timing: Timing | None = None, duration_s: int | None = 600
) -> TestDocumentView:
    section = SectionView(
        id=uuid4(),
        position=0,
        title="Botany",
        instructions=None,
        duration_s=duration_s,
        questions=questions,
    )
    return TestDocumentView(
        id=uuid4(),
        title="Cell Biology",
        instructions=None,
        settings=settings(timing),
        revision=1,
        archived_at=None,
        last_assigned_at=None,
        updated_at=None,  # type: ignore[arg-type]
        sections=(section,),
    )


NUMERICAL = question(
    QuestionType.NUMERICAL,
    options=(),
    numeric_answer=Decimal("6.02"),
    solution=None,
    marks_override=Decimal(2),
)


def test_paper_has_resolved_marks_and_no_answers() -> None:
    frozen = freeze(document(question(), NUMERICAL))

    text = json.dumps(frozen.paper)
    assert not [word for word in ANSWER_WORDS if f'"{word}"' in text]
    first, second = paper_questions(frozen.paper)
    assert (first["marks"], first["negative_marks"], second["marks"]) == ("4", "1", "2")
    assert "options" not in second
    assert first["tag_ids"]
    assert frozen.total_duration_s == 3600


def test_the_key_and_solutions_hold_the_answers() -> None:
    mcq = question()

    frozen = freeze(document(mcq, NUMERICAL))

    entries = frozen.key_entries["entries"]
    assert entries[str(mcq.id)] == {"type": "MCQ", "correct_option_ids": [str(mcq.options[0].id)]}  # type: ignore[index]
    assert entries[str(NUMERICAL.id)] == {"type": "NUMERICAL", "answer": "6.02", "tolerance": "0"}  # type: ignore[index]
    assert list(frozen.solutions) == [str(mcq.id)]


def test_a_test_with_problems_cannot_be_frozen() -> None:
    with pytest.raises(TestHasProblems) as error:
        freeze(document(question(options=())))

    assert error.value.context["problems"]


@pytest.mark.parametrize(
    ("timing", "override", "total"),
    [
        (None, TimingOverride(TimingKind.TOTAL, duration_s=1800), 1800),
        (
            Timing(TimingKind.PER_QUESTION, default_question_s=30),
            TimingOverride(TimingKind.PER_QUESTION, default_question_s=90),
            90,
        ),
    ],
)
def test_timing_override_changes_the_paper_only(
    timing: Timing | None, override: TimingOverride, total: int
) -> None:
    frozen = freeze(document(question(), timing=timing), override)

    assert frozen.total_duration_s == total
    assert frozen.paper["timing"]["total_duration_s"] == total  # type: ignore[index]


def test_section_durations_can_be_overridden() -> None:
    doc = document(question(), timing=Timing(TimingKind.SECTIONED))
    section_id = doc.sections[0].id

    frozen = freeze(
        doc, TimingOverride(TimingKind.SECTIONED, section_durations_s={section_id: 1200})
    )

    assert frozen.total_duration_s == 1200
    assert frozen.paper["sections"][0]["duration_s"] == 1200  # type: ignore[index]


def test_override_must_keep_the_timing_kind() -> None:
    with pytest.raises(FieldsInvalid):
        freeze(document(question()), TimingOverride(TimingKind.SECTIONED))


def test_a_test_without_a_known_length_cannot_be_frozen() -> None:
    # Per-question timing with no time anywhere: no problem is listed, but no paper can be built
    untimed = document(question(), timing=Timing(TimingKind.PER_QUESTION))

    with pytest.raises(TestHasProblems):
        freeze(untimed)
