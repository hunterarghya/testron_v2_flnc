from uuid import UUID

from django.db import transaction

from core.context import Ctx
from modules.assignments.repositories import assignments
from modules.assignments.services.changes import lock_for_change
from modules.assignments.services.inputs import password_token


def set_password(
    ctx: Ctx, *, assignment_id: UUID, password: str | None, password_confirm: str | None
) -> None:
    """Set, change or (with None) remove the test password, at any time until it is
    cancelled (D-07, domain_model.md §3.5 #4). Stored encrypted."""
    token = password_token(password, password_confirm)
    with transaction.atomic():
        lock_for_change(ctx, assignment_id, ["password"])
        assignments.set_password_token(assignment_id, token, now=ctx.now)
