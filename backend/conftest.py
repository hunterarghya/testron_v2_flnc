"""Fixtures for every test, in every module (testing_strategy.md §5)."""

import os
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from hypothesis import settings as hypothesis_settings

from core.clock import FrozenClock, use_clock

# The instant every frozen test starts at, unless the test moves the clock
TEST_NOW = datetime(2026, 11, 12, 4, 30, tzinfo=UTC)

# CI runs the same examples every time, so a red build is reproducible
hypothesis_settings.register_profile("ci", derandomize=True, deadline=None, print_blob=True)
hypothesis_settings.register_profile("dev", deadline=None)
hypothesis_settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "dev"))


@pytest.fixture
def frozen_clock() -> Iterator[FrozenClock]:
    """Time stands still at TEST_NOW; move it with `frozen_clock.advance(minutes=5)`."""
    clock = FrozenClock(TEST_NOW)
    with use_clock(clock):
        yield clock
