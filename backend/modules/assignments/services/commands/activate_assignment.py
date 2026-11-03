from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments.domain.entry import ensure_activatable, entry_window
from modules.assignments.policies import ensure_teacher
from modules.assignments.repositories import assignments, extensions


@dataclass(frozen=True, slots=True)
class Activation:
    activated_at: datetime
    # The shared clock's start (None for windows where each student has their own)
    anchor_at: datetime | None
    ends_at: datetime | None


def activate_assignment(ctx: Ctx, *, assignment_id: UUID) -> Activation:
    """Start for everyone (T-09): the server's time becomes the start, and waiting students
    get in within one gate poll. Pressing it again changes nothing (idempotent)."""
    ensure_teacher(ctx.actor)
    with transaction.atomic():
        record = assignments.lock_record(assignment_id)
        ensure_activatable(record.timeline)
        if record.timeline.activated_at is None:
            assignments.mark_activated(assignment_id, now=ctx.now)
            record = assignments.get_record(assignment_id)
    entry = entry_window(
        record.timeline, extensions.grants_by_assignment([assignment_id]).get(assignment_id, [])
    )
    activated_at = record.timeline.activated_at or ctx.now
    return Activation(activated_at=activated_at, anchor_at=entry.anchor_at, ends_at=entry.ends_at)
