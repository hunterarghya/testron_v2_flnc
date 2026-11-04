from uuid import UUID

from modules.students.repositories import students


def is_performance_shared(student_id: UUID) -> bool:
    """P-10 shows only while the teacher shares it (I-3, security.md A-11). No policy here:
    the caller is results' student use case, which checks the student first."""
    return students.is_performance_shared(student_id)
