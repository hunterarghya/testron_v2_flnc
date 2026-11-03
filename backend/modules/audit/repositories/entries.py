from collections.abc import Mapping
from datetime import datetime
from uuid import UUID

from modules.audit.models import AuditEntry


def insert_entry(
    *,
    actor_id: UUID | None,
    action: str,
    target_type: str,
    target_id: UUID,
    data: Mapping[str, object],
    at: datetime,
) -> None:
    AuditEntry.objects.create(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        data=dict(data),
        at=at,
    )


def entries_for(
    target_type: str, target_id: UUID
) -> list[tuple[str, UUID | None, dict[str, object]]]:
    """(action, actor, data) for one target, newest first."""
    rows = AuditEntry.objects.filter(target_type=target_type, target_id=target_id).order_by(
        "-at", "-id"
    )
    return [(row.action, row.actor_id, row.data) for row in rows]
