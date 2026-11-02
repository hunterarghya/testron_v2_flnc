"""Marking table (domain_model.md §6.1): one row per rule, NTA-style MSQ partial marks."""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

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
