from uuid import UUID

from django.db import transaction

from core.context import Ctx
from core.errors import FieldError, FieldsInvalid
from core.text import clean_text_line
from modules.audit import public as audit
from modules.delivery.domain.values import EndReason
from modules.delivery.policies import ensure_teacher
from modules.delivery.repositories import attempt_rows, attempts
from modules.delivery.repositories.attempt_rows import AttemptRow

OVERRIDE_ACTION = "attempt.disqualification_overridden"
MAX_REASON_LENGTH = 500


def override_disqualification(ctx: Ctx, *, attempt_id: UUID, reason: str) -> AttemptRow:
    """D-09 [G-2] (domain_model.md §6.3): a disqualified attempt counts again, in ranks and
    for the student, with its score as graded. The reason is kept in the audit log. Only a
    disqualified attempt can be overridden; repeating it keeps the first override."""
    ensure_teacher(ctx.actor)
    why = clean_text_line(reason)
    if not why or len(why) > MAX_REASON_LENGTH:
        raise FieldsInvalid(FieldError("reason", "invalid", "Say why, in up to 500 characters"))
    with transaction.atomic():
        attempts.lock_any(attempt_id)
        row = attempt_rows.row_of(attempt_id)
        if row.end_reason is not EndReason.DISQUALIFIED:
            raise FieldsInvalid(
                FieldError("attempt", "not_disqualified", "This attempt wasn't disqualified")
            )
        attempts.mark_overridden(attempt_id, now=ctx.now)
        audit.record(
            ctx,
            action=OVERRIDE_ACTION,
            target_type="attempt",
            target_id=attempt_id,
            data={"reason": why},
        )
    return row
