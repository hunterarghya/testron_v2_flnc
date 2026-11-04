"""Ranks, stats and visibility for an assignment's attempts, worked out on read
(domain_model.md §6.3-6.4). Shared by the gradebook, answer sheets and the student's views."""

from collections.abc import Sequence
from datetime import datetime

from modules.assignments import public as assignments
from modules.delivery import public as delivery
from modules.results.domain.ranking import Scored, is_counted, placings, pool_stats
from modules.results.domain.visibility import GradedTimes, PublicationTerms, result_visible
from modules.results.services.result_view import Ranked


def is_disqualified(attempt: delivery.AttemptRow) -> bool:
    return attempt.end_reason is not None and attempt.end_reason.value == "DISQUALIFIED"


def counts(attempt: delivery.AttemptRow) -> bool:
    return is_counted(
        ended=attempt.ended_at is not None,
        graded=attempt.graded_at is not None,
        disqualified=is_disqualified(attempt),
        overridden=attempt.disqualification_overridden_at is not None,
    )


def scored(attempts: Sequence[delivery.AttemptRow]) -> list[Scored]:
    return [Scored(a.id, a.take_number, a.score, counts(a)) for a in attempts]


def ranked(attempt: delivery.AttemptRow, everyone: Sequence[delivery.AttemptRow]) -> Ranked:
    """This attempt's place among the counted attempts of its take, and that pool's stats."""
    pool = scored(everyone)
    return Ranked(placings(pool).get(attempt.id), pool_stats(pool, attempt.take_number))


def terms(frame: assignments.ResultsFrame) -> PublicationTerms:
    record = frame.row.record
    publication = record.settings.publication
    return PublicationTerms(
        mode=publication.mode.value,
        delay_s=publication.delay_s,
        published_at=record.published_at,
        test_end=frame.row.ends_at,
    )


def is_visible(
    frame: assignments.ResultsFrame, attempt: delivery.AttemptRow, *, now: datetime
) -> bool:
    return result_visible(terms(frame), GradedTimes(attempt.ended_at, attempt.graded_at), now=now)
