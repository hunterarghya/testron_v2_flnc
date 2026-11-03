from uuid import UUID

from modules.assignments.repositories import assignments
from modules.assignments.services.student_views import StudentAssignment, student_assignments


def list_student_assignments(student_id: UUID) -> list[StudentAssignment]:
    """Every assignment the student is in and that isn't cancelled (A-01), newest first.
    Four queries. No policy here: the caller is delivery's list_my_tests, which checks the
    student first."""
    return student_assignments(assignments.list_records_for_student(student_id), student_id)
