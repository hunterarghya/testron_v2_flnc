"""The database rules of the assignment tables (database_schema.md §3.5)."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from core.clock import now
from modules.assignments.models import Assignment, Paper
from tests.factories.authoring import make_test

pytestmark = pytest.mark.django_db
NOW = now()


def make_assignment(**fields: object) -> Assignment:
    values: dict[str, object] = {
        "test": make_test(),
        "title": "Cell Biology",
        "window_kind": "OPEN",
        "requires_activation": False,
        "timing_kind": "TOTAL",
        "total_duration_s": 3600,
        "integrity_grace_s": 5,
        "integrity_max_warnings": 3,
        "integrity_action": "AUTO_SUBMIT",
        "publication_mode": "MANUAL",
        "publish_content": "SCORE_ONLY",
        "show_paper": False,
        "show_solutions": False,
        "show_rank_and_stats": False,
    }
    return Assignment.objects.create(**(values | fields))


@pytest.mark.parametrize(
    "fields",
    [
        {"window_kind": "OPEN", "starts_at": now()},
        {"window_kind": "SCHEDULED"},
        {"window_kind": "DEADLINE", "opens_at": NOW, "closes_at": NOW},
        {"window_kind": "DEADLINE", "opens_at": NOW},
        {
            "window_kind": "DEADLINE",
            "opens_at": now(),
            "closes_at": now() + timedelta(hours=1),
            "late_entry_s": 60,
        },
        {"window_kind": "MANUAL", "opens_at": now()},
        {"publication_mode": "AUTO_DELAYED"},
        {"publication_mode": "MANUAL", "publication_delay_s": 60},
        {"activated_at": now(), "cancelled_at": now()},
    ],
)
def test_the_database_refuses_bad_shapes(fields: dict[str, object]) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        make_assignment(**fields)


def test_each_window_kind_with_its_own_fields_is_accepted() -> None:
    soon = now() + timedelta(hours=1)
    make_assignment(window_kind="MANUAL", planned_at=soon, late_entry_s=600)
    make_assignment(window_kind="SCHEDULED", starts_at=soon)
    make_assignment(window_kind="DEADLINE", opens_at=soon, closes_at=soon + timedelta(hours=2))
    make_assignment(publication_mode="AUTO_DELAYED", publication_delay_s=3600)

    assert Assignment.objects.count() == 4


def test_a_paper_can_never_change() -> None:
    paper = Paper.objects.create(
        assignment=make_assignment(),
        content={"v": 1, "marks": str(Decimal(4))},
        content_hash="x" * 64,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        Paper.objects.filter(pk=paper.pk).update(content={"v": 1, "marks": "100"})

    paper.refresh_from_db()
    assert paper.content["marks"] == "4"
