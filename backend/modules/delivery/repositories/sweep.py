from datetime import datetime
from uuid import UUID

from modules.delivery.domain.values import AttemptStatus
from modules.delivery.models import Attempt


def in_progress_ids(*, anchored_before: datetime | None, limit: int | None) -> list[UUID]:
    """Sittings still running, oldest first (the `attempts_in_progress_anchor` index)."""
    rows = Attempt.objects.filter(status=AttemptStatus.IN_PROGRESS)
    if anchored_before is not None:
        rows = rows.filter(anchor_at__lt=anchored_before)
    ids = rows.order_by("anchor_at").values_list("id", flat=True)
    return list(ids[:limit] if limit is not None else ids)
