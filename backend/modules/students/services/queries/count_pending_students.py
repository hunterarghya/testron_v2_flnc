from core.context import StudentStatus
from modules.students.repositories import students


def count_pending_students() -> int:
    """How many join requests wait for the teacher (the Students badge, T-01 attention).
    No policy here: callers are other modules' use cases, which check the teacher first."""
    return students.count_with_status(StudentStatus.PENDING)
