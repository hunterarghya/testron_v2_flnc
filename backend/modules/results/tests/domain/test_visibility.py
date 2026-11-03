"""The visibility table (domain_model.md §6.4; E-27, E-28; testing_strategy.md §3.1)."""

from datetime import UTC, datetime, timedelta

import pytest

from modules.results.domain.visibility import (
    GradedTimes,
    PublicationTerms,
    publish_at,
    result_visible,
)

T = datetime(2026, 11, 12, 6, 0, tzinfo=UTC)
H = timedelta(hours=1)
ENDED = GradedTimes(ended_at=T, graded_at=T)
RUNNING = GradedTimes(ended_at=None, graded_at=None)


def terms(
    mode: str,
    *,
    delay: int | None = None,
    published: datetime | None = None,
    end: datetime | None = T,
) -> PublicationTerms:
    return PublicationTerms(mode=mode, delay_s=delay, published_at=published, test_end=end)


@pytest.mark.parametrize(
    ("name", "publication", "attempt", "now", "visible"),
    [
        ("manual_not_published", terms("MANUAL"), ENDED, T + H, False),
        ("manual_published", terms("MANUAL", published=T + H), ENDED, T + 2 * H, True),
        (
            "manual_published_later_than_now",
            terms("MANUAL", published=T + 2 * H),
            ENDED,
            T + H,
            False,
        ),
        ("manual_unpublished_again_e28", terms("MANUAL", published=None), ENDED, T + 9 * H, False),
        ("manual_published_but_still_sitting", terms("MANUAL", published=T), RUNNING, T + H, False),
        ("immediate_once_graded", terms("AUTO_IMMEDIATE"), ENDED, T, True),
        ("immediate_while_sitting", terms("AUTO_IMMEDIATE"), RUNNING, T + H, False),
        ("immediate_ended_not_graded", terms("AUTO_IMMEDIATE"), GradedTimes(T, None), T + H, False),
        (
            "delayed_before_the_delay",
            terms("AUTO_DELAYED", delay=3600),
            ENDED,
            T + H - timedelta(seconds=1),
            False,
        ),
        ("delayed_at_the_delay", terms("AUTO_DELAYED", delay=3600), ENDED, T + H, True),
        (
            "delayed_counts_from_the_common_end",
            terms("AUTO_DELAYED", delay=600, end=T + H),
            ENDED,
            T + H,
            False,
        ),
        (
            "delayed_after_the_common_end",
            terms("AUTO_DELAYED", delay=600, end=T + H),
            ENDED,
            T + 2 * H,
            True,
        ),
        (
            "delayed_open_window_per_student_e27",
            terms("AUTO_DELAYED", delay=600, end=None),
            ENDED,
            T + H,
            True,
        ),
        (
            "delayed_open_window_still_sitting",
            terms("AUTO_DELAYED", delay=600, end=None),
            RUNNING,
            T + H,
            False,
        ),
        (
            "delayed_ignores_a_publish_stamp",
            terms("AUTO_DELAYED", delay=7200, published=T),
            ENDED,
            T + H,
            False,
        ),
        (
            "immediate_ignores_no_publish_stamp",
            terms("AUTO_IMMEDIATE", published=None),
            ENDED,
            T + H,
            True,
        ),
    ],
)
def test_result_visible(
    name: str, publication: PublicationTerms, attempt: GradedTimes, now: datetime, visible: bool
) -> None:
    assert result_visible(publication, attempt, now=now) is visible, name


def test_publish_at() -> None:
    assert publish_at(terms("AUTO_DELAYED", delay=600, end=None), RUNNING) is None
    assert publish_at(terms("AUTO_IMMEDIATE"), ENDED) == T
    assert publish_at(terms("MANUAL", published=T + H), ENDED) == T + H
