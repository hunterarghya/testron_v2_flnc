"""What the teacher may still change, and when results come out (domain_model.md §3.5 #5-6,
§7). `editable_fields` also drives which inputs the overview enables (T-08)."""

from collections.abc import Collection
from datetime import datetime, timedelta
from enum import StrEnum

from modules.assignments.domain.errors import (
    AssignmentCancelled,
    AssignmentHasAttempts,
    AssignmentStarted,
)
from modules.assignments.domain.lifecycle import Timeline
from modules.assignments.domain.settings import Publication
from modules.assignments.domain.values import PublicationMode

BEFORE_START = ("title", "window", "gate", "integrity", "publication", "audience", "password")
# "audience" is replacing the whole list. Adding students, and removing those who never
# began (E-11), stay possible until the assignment is cancelled.
AFTER_START = ("title", "publication", "password")


class PublicationState(StrEnum):
    UNPUBLISHED = "UNPUBLISHED"
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"


def editable_fields(*, cancelled: bool, started: bool) -> tuple[str, ...]:
    if cancelled:
        return ()
    return AFTER_START if started else BEFORE_START


def ensure_editable(changed: Collection[str], *, cancelled: bool, started: bool) -> None:
    if cancelled:
        raise AssignmentCancelled()
    allowed = editable_fields(cancelled=cancelled, started=started)
    if not set(changed) <= set(allowed):
        raise AssignmentStarted(allowed)


def ensure_cancellable(timeline: Timeline, *, has_attempts: bool) -> None:
    """Only while no one has begun, and never after Start (domain_model.md §3.5 #6)."""
    if timeline.cancelled_at is not None:
        raise AssignmentCancelled()
    if has_attempts:
        raise AssignmentHasAttempts()
    if timeline.activated_at is not None:
        raise AssignmentStarted(AFTER_START)


def publication_state(publication: Publication, published_at: datetime | None) -> PublicationState:
    if published_at is not None:
        return PublicationState.PUBLISHED
    if publication.mode is PublicationMode.MANUAL:
        return PublicationState.UNPUBLISHED
    return PublicationState.SCHEDULED


def publish_at(publication: Publication, end: datetime | None) -> datetime | None:
    """When automatic publication will happen: at the end, or that long after it."""
    if publication.mode is PublicationMode.MANUAL or end is None:
        return None
    return end + timedelta(seconds=publication.delay_s or 0)
