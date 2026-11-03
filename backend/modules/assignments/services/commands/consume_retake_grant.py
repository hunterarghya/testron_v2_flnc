from uuid import UUID

from modules.assignments.repositories import retake_grants


def consume_retake_grant(assignment_id: UUID, student_id: UUID, *, attempt_id: UUID) -> bool:
    """A granted sitting uses up the oldest unused grant, in the caller's transaction
    (domain_model.md §3.6 #2). No policy: the caller is delivery's start, after its checks.
    False when another start used it first."""
    return retake_grants.consume_oldest(assignment_id, student_id, attempt_id=attempt_id)
