from uuid import UUID

from modules.audit import public as audit
from modules.delivery.services.commands.override_disqualification import OVERRIDE_ACTION


def get_override_reason(attempt_id: UUID) -> str | None:
    """Why the teacher counted a disqualified attempt (D-09), from the audit log; None if they
    never did. No policy: the caller is results' teacher use case, which checks first."""
    found = (
        data.get("reason")
        for action, _, data in audit.entries_for("attempt", attempt_id)
        if action == OVERRIDE_ACTION
    )
    # Overriding twice keeps the first, so the oldest entry is the one that counted
    reasons = [str(reason) for reason in found if reason]
    return reasons[-1] if reasons else None
