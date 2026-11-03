"""Checks on the teacher's live controls (D-02, D-03)."""

from uuid import uuid4

import pytest

from core.errors import FieldsInvalid
from modules.assignments.domain.live_controls import (
    AssignmentNotStarted,
    ensure_extension_valid,
    ensure_started,
    plan_grants,
)


def test_controls_need_a_started_test() -> None:
    ensure_started(True)
    with pytest.raises(AssignmentNotStarted):
        ensure_started(False)


def test_every_extension_problem_at_once() -> None:
    ensure_extension_valid(600, None, stage_count=2, unknown_students=[])
    ensure_extension_valid(86_400, 1, stage_count=2, unknown_students=[])
    with pytest.raises(FieldsInvalid) as bad:
        ensure_extension_valid(0, 2, stage_count=2, unknown_students=[uuid4()])
    assert [e.field for e in bad.value.field_errors()] == ["seconds", "stage_index", "student_ids"]


def test_grants_go_to_the_audience_once_each() -> None:
    a, b, stranger = uuid4(), uuid4(), uuid4()
    outcome = plan_grants([a, stranger, a, b], {a, b})
    assert outcome.applied == (a, b)
    assert [(s.student_id, s.reason) for s in outcome.skipped] == [(stranger, "not_found")]
