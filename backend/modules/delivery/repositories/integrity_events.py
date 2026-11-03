from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from core.ids import uuid7
from modules.delivery.domain.values import IntegrityKind
from modules.delivery.models import IntegrityEvent


def record_device_change(attempt_id: UUID, *, now: datetime) -> None:
    """The teacher sees "device changed"; it is never a warning (domain_model.md §5.9)."""
    IntegrityEvent.objects.create(
        id=uuid7(),
        attempt_id=attempt_id,
        kind=IntegrityKind.DEVICE_CHANGED.value,
        left_at=now,
        returned_at=now,
        reported_at=now,
    )


def find(event_id: UUID) -> tuple[UUID, bool] | None:
    """The event's attempt and whether it was counted; None if it was never reported."""
    return IntegrityEvent.objects.filter(pk=event_id).values_list("attempt_id", "counted").first()


def insert_event(  # keyword-only after the ids (CLAUDE.md limits)
    event_id: UUID,
    attempt_id: UUID,
    *,
    kind: IntegrityKind,
    left_at: datetime,
    now: datetime,
) -> None:
    IntegrityEvent.objects.create(
        id=event_id, attempt_id=attempt_id, kind=kind.value, left_at=left_at, reported_at=now
    )


def mark_returned(event_id: UUID, *, returned_at: datetime) -> None:
    """The first return time stays: a later retry of the same report changes nothing."""
    IntegrityEvent.objects.filter(pk=event_id, returned_at__isnull=True).update(
        returned_at=returned_at
    )


def mark_counted(event_id: UUID) -> None:
    IntegrityEvent.objects.filter(pk=event_id).update(counted=True)


@dataclass(frozen=True, slots=True)
class EventRow:
    kind: IntegrityKind
    left_at: datetime
    returned_at: datetime | None
    counted: bool


def of_attempt(attempt_id: UUID) -> list[EventRow]:
    rows = (
        IntegrityEvent.objects.filter(attempt_id=attempt_id)
        .order_by("left_at")
        .values_list("kind", "left_at", "returned_at", "counted")
    )
    return [
        EventRow(IntegrityKind(kind), left, back, counted) for kind, left, back, counted in rows
    ]
