"""Marking table (domain_model.md §6.1): one row per rule, NTA-style MSQ partial marks."""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st

from modules.grading.domain.marking import (
    Mark,
    Outcome,
    mark_mcq,
    mark_msq,
    mark_numerical,
)

A, B, C, D = (uuid4() for _ in range(4))
FOUR, ONE, ZERO = Decimal(4), Decimal(1), Decimal(0)


@pytest.mark.parametrize(
    ("selected", "negative", "expected"),
    [
        (set(), ONE, Mark(Outcome.UNANSWERED, Decimal("0.00"))),
        ({A, B, C}, ONE, Mark(Outcome.CORRECT, Decimal("4.00"))),
        # 2 of 3 correct options, no wrong one: 2 * 4/3
        ({A, B}, ONE, Mark(Outcome.PARTIAL, Decimal("2.67"))),
        ({A}, ONE, Mark(Outcome.PARTIAL, Decimal("1.33"))),
        # One wrong option, whatever else: the full penalty
        ({A, B, D}, ONE, Mark(Outcome.INCORRECT, Decimal("-1.00"))),
        ({D}, ONE, Mark(Outcome.INCORRECT, Decimal("-1.00"))),
        ({A, B, C, D}, ONE, Mark(Outcome.INCORRECT, Decimal("-1.00"))),
        # No negative marking: a wrong pick scores 0
        ({A, D}, ZERO, Mark(Outcome.INCORRECT, Decimal("0.00"))),
    ],
)
def test_msq(selected: set[UUID], negative: Decimal, expected: Mark) -> None:
    assert mark_msq(selected, {A, B, C}, marks=FOUR, negative=negative) == expected


def test_msq_with_every_option_correct_and_all_picked_is_correct() -> None:
    assert mark_msq({A, B}, {A, B}, marks=FOUR, negative=ONE).outcome is Outcome.CORRECT


@pytest.mark.parametrize(
    ("selected", "expected"),
    [
        (set(), Mark(Outcome.UNANSWERED, Decimal("0.00"))),
        ({A}, Mark(Outcome.CORRECT, Decimal("4.00"))),
        ({B}, Mark(Outcome.INCORRECT, Decimal("-1.00"))),
    ],
)
def test_mcq(selected: set[UUID], expected: Mark) -> None:
    assert mark_mcq(selected, {A}, marks=FOUR, negative=ONE) == expected


@pytest.mark.parametrize(
    ("value", "tolerance", "outcome"),
    [
        (None, ZERO, Outcome.UNANSWERED),
        (Decimal("46.0"), ZERO, Outcome.CORRECT),
        (Decimal("46.01"), ZERO, Outcome.INCORRECT),
        (Decimal("46.01"), Decimal("0.01"), Outcome.CORRECT),
    ],
)
def test_numerical(value: Decimal | None, tolerance: Decimal, outcome: Outcome) -> None:
    mark = mark_numerical(value, Decimal(46), tolerance=tolerance, marks=FOUR, negative=ONE)

    assert mark.outcome is outcome


@pytest.mark.parametrize(
    ("value", "answer", "tolerance", "outcome"),
    [
        # E-17: equal as decimals whatever the trailing zeros
        (Decimal("46.00"), Decimal(46), ZERO, Outcome.CORRECT),
        (Decimal("-12.5"), Decimal("-12.50"), ZERO, Outcome.CORRECT),
        # Tolerance edges: exactly at the edge counts, just outside doesn't
        (Decimal("46.5"), Decimal(46), Decimal("0.5"), Outcome.CORRECT),
        (Decimal("45.5"), Decimal(46), Decimal("0.5"), Outcome.CORRECT),
        (Decimal("46.500001"), Decimal(46), Decimal("0.5"), Outcome.INCORRECT),
        (Decimal(-46), Decimal(46), ZERO, Outcome.INCORRECT),
    ],
)
def test_numerical_edges(
    value: Decimal, answer: Decimal, tolerance: Decimal, outcome: Outcome
) -> None:
    assert (
        mark_numerical(value, answer, tolerance=tolerance, marks=FOUR, negative=ONE).outcome
        is outcome
    )


@pytest.mark.parametrize(
    ("marks", "picked", "correct", "expected"),
    [
        # Rounded once, half up, to 0.01
        (Decimal("2.5"), {A}, {A, B, C}, Decimal("0.83")),
        (Decimal(1), {A, B}, {A, B, C}, Decimal("0.67")),
        (Decimal("0.5"), {A}, {A, B, C, D}, Decimal("0.13")),
    ],
)
def test_partial_marks_are_rounded_half_up(
    marks: Decimal, picked: set[UUID], correct: set[UUID], expected: Decimal
) -> None:
    assert mark_msq(picked, correct, marks=marks, negative=ONE).marks == expected


def test_mcq_with_two_picks_is_incorrect() -> None:
    assert mark_mcq({A, B}, {A}, marks=FOUR, negative=ONE) == Mark(
        Outcome.INCORRECT, Decimal("-1.00")
    )


def test_fractional_negative_marks_are_kept() -> None:
    assert mark_mcq({B}, {A}, marks=FOUR, negative=Decimal("0.25")).marks == Decimal("-0.25")


options = st.sets(st.sampled_from([A, B, C, D]))
amounts = st.decimals(min_value=0, max_value=100, places=2)


@given(options, options.filter(bool), amounts, amounts)
def test_marks_stay_between_minus_n_and_m(
    picked: set[UUID], correct: set[UUID], marks: Decimal, negative: Decimal
) -> None:
    for mark in (
        mark_msq(picked, correct, marks=marks, negative=negative),
        mark_mcq(picked, correct, marks=marks, negative=negative),
    ):
        assert -negative <= mark.marks <= marks


@given(options.filter(bool), amounts)
def test_msq_partial_grows_with_each_correct_pick(correct: set[UUID], marks: Decimal) -> None:
    ordered = sorted(correct, key=str)
    scores = [
        mark_msq(set(ordered[:n]), correct, marks=marks, negative=ONE).marks
        for n in range(1, len(ordered) + 1)
    ]
    assert scores == sorted(scores)
