from datetime import UTC, datetime

from django.db import models

from core.clock import FrozenClock, use_clock
from core.db.base_model import TimestampedModel
from core.db.locking import for_share, for_update, skip_locked

NOON = datetime(2026, 11, 12, 4, 30, tzinfo=UTC)


class Sample(TimestampedModel):
    name = models.TextField()

    class Meta:
        app_label = "core_tests"


def test_new_row_gets_a_uuid7_key() -> None:
    assert Sample().id.version == 7


def test_new_row_times_come_from_the_clock() -> None:
    with use_clock(FrozenClock(NOON)):
        row = Sample()

    assert row.created_at == row.updated_at == NOON


def test_for_update_locks_only_this_table() -> None:
    query = for_update(Sample.objects.all()).query

    assert query.select_for_update
    assert query.select_for_update_of == ("self",)
    assert not query.select_for_no_key_update
    assert not query.select_for_update_skip_locked


def test_for_share_takes_a_no_key_lock() -> None:
    query = for_share(Sample.objects.all()).query

    assert query.select_for_no_key_update
    assert query.select_for_update_of == ("self",)


def test_skip_locked_skips_rows_held_elsewhere() -> None:
    query = skip_locked(Sample.objects.all()).query

    assert query.select_for_update_skip_locked
    assert query.select_for_update_of == ("self",)
