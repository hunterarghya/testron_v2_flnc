"""Fixtures for every test, in every module (testing_strategy.md §5)."""

import os
import re
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager
from datetime import UTC, datetime
from typing import Any

import pytest
from django.core import mail
from hypothesis import settings as hypothesis_settings

from core.clock import FrozenClock, use_clock
from core.context import ANONYMOUS, Actor, Ctx

# The instant every frozen test starts at, unless the test moves the clock
TEST_NOW = datetime(2026, 11, 12, 4, 30, tzinfo=UTC)

# CI runs the same examples every time, so a red build is reproducible
hypothesis_settings.register_profile("ci", derandomize=True, deadline=None, print_blob=True)
hypothesis_settings.register_profile("dev", deadline=None)
hypothesis_settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "dev"))

MakeCtx = Callable[..., Ctx]
AfterCommit = Callable[[], AbstractContextManager[object]]


@pytest.fixture
def frozen_clock() -> Iterator[FrozenClock]:
    """Time stands still at TEST_NOW; move it with `frozen_clock.advance(minutes=5)`."""
    clock = FrozenClock(TEST_NOW)
    with use_clock(clock):
        yield clock


@pytest.fixture
def make_ctx(frozen_clock: FrozenClock) -> MakeCtx:
    """`make_ctx()` is an anonymous request now; `make_ctx(actor)` is someone else's."""

    def build(actor: Actor = ANONYMOUS) -> Ctx:
        return Ctx(actor=actor, now=frozen_clock.now(), request_id="req-test")

    return build


@pytest.fixture
def after_commit(
    django_capture_on_commit_callbacks: Callable[..., AbstractContextManager[Any]],
) -> AfterCommit:
    """`with after_commit():` runs the code, then what it scheduled for after the commit
    (e.g. sending an email), as a real commit would."""
    return lambda: django_capture_on_commit_callbacks(execute=True)


def last_emailed_code() -> str:
    """The 6-digit code in the most recent email."""
    found = re.search(r"\b(\d{6})\b", str(mail.outbox[-1].body))
    if found is None:
        raise AssertionError("the last email has no 6-digit code")
    return found.group(1)
