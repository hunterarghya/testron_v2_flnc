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
