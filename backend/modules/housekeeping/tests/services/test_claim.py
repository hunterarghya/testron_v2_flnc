"""Only one request in ten minutes gets to run housekeeping (architecture.md §5.6)."""

from datetime import UTC, datetime, timedelta

import pytest

from modules.housekeeping.domain.schedule import cutoffs
from modules.housekeeping.repositories import runs

pytestmark = pytest.mark.django_db
NOW = datetime(2026, 11, 12, 4, 30, tzinfo=UTC)


def claim(at: datetime) -> bool:
    return runs.claim(now=at, due_after=cutoffs(at).due_after)


def test_the_first_request_claims_then_nobody_until_ten_minutes_pass() -> None:
    assert claim(NOW) is True
    assert claim(NOW + timedelta(minutes=9, seconds=59)) is False
    assert claim(NOW + timedelta(minutes=10)) is True
    assert claim(NOW + timedelta(minutes=11)) is False
