"""When housekeeping runs and what counts as old (database_schema.md §5.4)."""

from datetime import UTC, datetime, timedelta

from modules.housekeeping.domain.schedule import cutoffs

NOW = datetime(2026, 11, 12, 4, 30, tzinfo=UTC)


def test_cutoffs_follow_the_documented_ages() -> None:
    due = cutoffs(NOW)

    assert NOW - due.due_after == timedelta(minutes=10)
    assert NOW - due.otps_before == timedelta(days=7)
    assert NOW - due.rate_limits_before == timedelta(days=1)
    assert NOW - due.abandoned_before == timedelta(hours=24)
