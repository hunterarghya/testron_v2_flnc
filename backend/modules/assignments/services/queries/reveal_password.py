from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments.policies import ensure_teacher
from modules.assignments.repositories import assignments
from modules.assignments.services.password_cipher import decrypt_password
from modules.audit import public as audit

REVEAL_ACTION = "assignment.password_revealed"


def reveal_password(ctx: Ctx, *, assignment_id: UUID) -> str | None:
    """The test password as the teacher typed it, or None if there is none (T-08, T-09 👁).
    Every reveal is written to the audit log (domain_model.md §3.5 #4, security.md T-06)."""
    ensure_teacher(ctx.actor)
    with transaction.atomic():
        token = assignments.get_password_token(assignment_id)
        audit.record(ctx, action=REVEAL_ACTION, target_type="assignment", target_id=assignment_id)
    return None if token is None else decrypt_password(token)
