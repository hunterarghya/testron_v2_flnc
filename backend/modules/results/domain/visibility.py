"""When a student may see a result (domain_model.md §6.4): one rule, used everywhere a result
is read. Automatic publishing needs no job: it is this comparison with `now`.

    MANUAL          -> when the teacher published (never, until they do)
    AUTO_IMMEDIATE  -> as soon as the attempt is graded
    AUTO_DELAYED(d) -> d after the test ends for everyone, or after this attempt ended
                       when there is no common end (an open window: per student)
"""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True, slots=True)
class PublicationTerms:
    mode: str
    delay_s: int | None
    # Set by Publish; cleared by Unpublish
    published_at: datetime | None
    # When the test ends for everyone; None for an open window
    test_end: datetime | None


@dataclass(frozen=True, slots=True)
class GradedTimes:
    ended_at: datetime | None
    graded_at: datetime | None


def publish_at(terms: PublicationTerms, attempt: GradedTimes) -> datetime | None:
    if terms.mode == "AUTO_IMMEDIATE":
        return attempt.graded_at
    if terms.mode == "AUTO_DELAYED":
        base = terms.test_end or attempt.ended_at
        return None if base is None else base + timedelta(seconds=terms.delay_s or 0)
    return terms.published_at


def result_visible(terms: PublicationTerms, attempt: GradedTimes, *, now: datetime) -> bool:
    if attempt.ended_at is None or attempt.graded_at is None:
        return False
    at = publish_at(terms, attempt)
    return at is not None and at <= now
