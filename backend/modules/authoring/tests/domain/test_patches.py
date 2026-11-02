"""Settings, section and question change rules (T-03, T-04)."""

from decimal import Decimal
from uuid import uuid4

import pytest

from core.errors import FieldsInvalid
from core.rich_content import EMPTY_DOC
from modules.authoring.domain.drafts import Integrity, Marking, TestSettings, Timing
from modules.authoring.domain.question_patch import (
    OptionInput,
    QuestionChanges,
    ensure_changes_valid,
    plan_options,
)
from modules.authoring.domain.section_rules import section_duration, section_title
from modules.authoring.domain.settings_patch import SettingsPatch, TimingPatch, apply_settings_patch
from modules.authoring.domain.values import IntegrityAction, QuestionType, TimingKind
from modules.authoring.tests.domain.drafts import settings

SECTIONED = Timing(TimingKind.SECTIONED)
PER_QUESTION = Timing(TimingKind.PER_QUESTION, default_question_s=30)


def fields_of(error: pytest.ExceptionInfo[FieldsInvalid]) -> list[str]:
    return [e.field for e in error.value.field_errors()]


@pytest.mark.parametrize(
    ("current", "patch", "expected"),
    [
        (
            settings(),
            TimingPatch(TimingKind.TOTAL, duration_s=1800),
            Timing(TimingKind.TOTAL, duration_s=1800),
        ),
        (
            settings(PER_QUESTION),
            TimingPatch(TimingKind.PER_QUESTION, default_question_s=45),
            Timing(TimingKind.PER_QUESTION, default_question_s=45),
        ),
        (
            settings(SECTIONED),
            TimingPatch(TimingKind.SECTIONED, allow_return=True),
            Timing(TimingKind.SECTIONED, allow_return=True),
        ),
        (settings(SECTIONED), TimingPatch(TimingKind.SECTIONED), SECTIONED),
    ],
)
def test_timing_values_change_within_a_kind(
    current: TestSettings, patch: TimingPatch, expected: Timing
) -> None:
    change = apply_settings_patch(current, SettingsPatch(timing=patch), section_durations=[None])

    assert (change.settings.timing, change.switch) == (expected, None)


def test_the_rest_of_the_settings_change_only_when_sent() -> None:
    integrity = Integrity(10, 5, IntegrityAction.DISQUALIFY)

    change = apply_settings_patch(
        settings(), SettingsPatch(shuffle_questions=True, integrity=integrity), section_durations=[]
    )

    assert (change.settings.shuffle_questions, change.settings.shuffle_options) == (True, False)
    assert (change.settings.integrity, change.settings.marking) == (integrity, settings().marking)


def test_every_bad_setting_is_reported() -> None:
    patch = SettingsPatch(
        timing=TimingPatch(TimingKind.PER_QUESTION, duration_s=10, default_question_s=1),
        marking=Marking(Decimal(0), Decimal(-1)),
        integrity=Integrity(61, 0, IntegrityAction.AUTO_SUBMIT),
    )

    with pytest.raises(FieldsInvalid) as error:
        apply_settings_patch(settings(), patch, section_durations=[])

    assert fields_of(error) == [
        "settings.timing.duration_s",
        "settings.timing.default_question_s",
        "settings.marking.marks",
        "settings.marking.negative_marks",
        "settings.integrity.grace_s",
        "settings.integrity.max_warnings",
    ]


def test_section_title_and_duration() -> None:
    assert section_title("  Botany   part 1 ") == "Botany part 1"
    assert (section_duration(None), section_duration(600)) == (None, 600)
    with pytest.raises(FieldsInvalid):
        section_title("x" * 121)
    with pytest.raises(FieldsInvalid):
        section_duration(30)


@pytest.mark.parametrize(
    ("final_type", "changes", "fields"),
    [
        (
            QuestionType.MCQ,
            {
                "marks_override": Decimal("0.5"),
                "negative_marks_override": Decimal(0),
                "time_override_s": 30,
            },
            [],
        ),
        (QuestionType.MCQ, {"negative_marks_override": Decimal(-1)}, ["negative_marks_override"]),
        (QuestionType.NUMERICAL, {"numeric_tolerance": Decimal(-1)}, ["numeric_tolerance"]),
        (QuestionType.NUMERICAL, {"options": [OptionInput(None, EMPTY_DOC, True)]}, ["options"]),
        (QuestionType.MSQ, {"options": [OptionInput(None, EMPTY_DOC, False)] * 11}, ["options"]),
        (QuestionType.MCQ, {"numeric_tolerance": Decimal("0.1")}, ["numeric_answer"]),
        (
            QuestionType.MCQ,
            {"chapter_tags": ["x"] * 21, "topic_tags": ["y"] * 21},
            ["chapter_tags", "topic_tags"],
        ),
    ],
)
def test_question_change_rules(
    final_type: QuestionType, changes: QuestionChanges, fields: list[str]
) -> None:
    if not fields:
        ensure_changes_valid(final_type, changes)
        return
    with pytest.raises(FieldsInvalid) as error:
        ensure_changes_valid(final_type, changes)
    assert fields_of(error) == fields


def test_options_plan_keeps_known_ids_adds_new_and_removes_the_rest() -> None:
    kept, dropped = uuid4(), uuid4()

    plan = plan_options(
        {kept, dropped}, [OptionInput(None, EMPTY_DOC, False), OptionInput(kept, EMPTY_DOC, True)]
    )

    assert [(row[0], row[1], row[3]) for row in plan.rows] == [(None, 0, False), (kept, 1, True)]
    assert plan.removed == {dropped}


def test_an_option_id_may_appear_once() -> None:
    kept = uuid4()

    with pytest.raises(FieldsInvalid) as error:
        plan_options(
            {kept}, [OptionInput(kept, EMPTY_DOC, True), OptionInput(kept, EMPTY_DOC, False)]
        )

    assert fields_of(error) == ["options.1.id"]
