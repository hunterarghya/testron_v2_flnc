"""Effective settings (domain_model.md §4.2), positions, reorders and the timing switch (§3.4)."""

from decimal import Decimal
from uuid import uuid4

import pytest

from core.errors import FieldsInvalid
from modules.authoring.domain.drafts import Timing
from modules.authoring.domain.effective import (
    effective_marks,
    effective_negative_marks,
    effective_time_s,
    total_duration_s,
    total_marks,
)
from modules.authoring.domain.structure import (
    DEFAULT_DURATION_S,
    DEFAULT_QUESTION_S,
    ensure_same_structure,
    insert_after,
    merged,
    positions,
    switch_timing,
)
from modules.authoring.domain.values import TimingKind
from modules.authoring.tests.domain.drafts import draft_of, mcq, section, settings

TOTAL = Timing(TimingKind.TOTAL, duration_s=3600)
PER_QUESTION = Timing(TimingKind.PER_QUESTION, default_question_s=30)
SECTIONED = Timing(TimingKind.SECTIONED, allow_return=True)


def test_overrides_win_over_the_test_defaults() -> None:
    plain, custom = mcq(), mcq(marks_override=Decimal(2), negative_marks_override=Decimal(0))
    defaults = settings()

    assert (effective_marks(plain, defaults), effective_negative_marks(plain, defaults)) == (
        Decimal(4),
        Decimal(1),
    )
    assert (effective_marks(custom, defaults), effective_negative_marks(custom, defaults)) == (
        Decimal(2),
        Decimal(0),
    )


def test_question_time_exists_only_per_question() -> None:
    assert effective_time_s(mcq(), settings(PER_QUESTION)) == 30
    assert effective_time_s(mcq(time_override_s=90), settings(PER_QUESTION)) == 90
    assert effective_time_s(mcq(time_override_s=90), settings(TOTAL)) is None


def test_totals_per_timing_kind() -> None:
    questions = (mcq(), mcq(time_override_s=90, marks_override=Decimal("2.5")))

    assert total_marks(draft_of(section(*questions))) == Decimal("6.5")
    assert total_duration_s(draft_of(section(*questions))) == 3600
    assert total_duration_s(draft_of(section(*questions), timing=PER_QUESTION)) == 120
    sectioned = draft_of(section(duration_s=600), section(duration_s=900), timing=SECTIONED)
    assert total_duration_s(sectioned) == 1500
    assert total_duration_s(draft_of(section(duration_s=600), section(), timing=SECTIONED)) is None


def test_insert_after_places_items() -> None:
    a, b, new = uuid4(), uuid4(), uuid4()

    assert insert_after([a, b], new, a) == [a, new, b]
    assert insert_after([a, b], new, b) == [a, b, new]
    assert insert_after([a, b], new, None) == [new, a, b]
    assert positions([b, a]) == {b: 0, a: 1}
    with pytest.raises(FieldsInvalid):
        insert_after([a], new, b)


def test_a_reorder_must_name_everything_exactly_once() -> None:
    s1, s2, q1, q2 = uuid4(), uuid4(), uuid4(), uuid4()
    current = [(s1, [q1]), (s2, [q2])]

    ensure_same_structure(current, [(s2, [q2, q1]), (s1, [])])
    for wrong in ([(s1, [q1, q2])], [(s1, [q1]), (s2, [q1])], [(s1, [q1, q2]), (s2, [q2])]):
        with pytest.raises(FieldsInvalid):
            ensure_same_structure(current, wrong)


def test_merging_keeps_question_order_in_the_first_section() -> None:
    s1, s2, q1, q2, q3 = uuid4(), uuid4(), uuid4(), uuid4(), uuid4()

    assert merged([(s1, [q1]), (s2, [q2, q3])]) == [(s1, [q1, q2, q3])]
    assert merged([]) == []


@pytest.mark.parametrize(
    ("current", "kind", "durations", "timing", "merge", "carried"),
    [
        (TOTAL, TimingKind.TOTAL, [None], TOTAL, False, None),
        (TOTAL, TimingKind.SECTIONED, [None], Timing(TimingKind.SECTIONED), False, 3600),
        (
            TOTAL,
            TimingKind.PER_QUESTION,
            [None],
            Timing(TimingKind.PER_QUESTION, default_question_s=DEFAULT_QUESTION_S),
            False,
            None,
        ),
        (
            SECTIONED,
            TimingKind.TOTAL,
            [600, 900],
            Timing(TimingKind.TOTAL, duration_s=1500),
            True,
            None,
        ),
        (
            SECTIONED,
            TimingKind.TOTAL,
            [600, None],
            Timing(TimingKind.TOTAL, duration_s=DEFAULT_DURATION_S),
            True,
            None,
        ),
        (
            PER_QUESTION,
            TimingKind.TOTAL,
            [None],
            Timing(TimingKind.TOTAL, duration_s=DEFAULT_DURATION_S),
            False,
            None,
        ),
    ],
)
def test_switching_timing(
    current: Timing,
    kind: TimingKind,
    durations: list[int | None],
    timing: Timing,
    merge: bool,
    carried: int | None,
) -> None:
    switch = switch_timing(current, kind, section_durations=durations)

    assert (switch.timing, switch.merge_sections, switch.section_duration_s) == (
        timing,
        merge,
        carried,
    )
