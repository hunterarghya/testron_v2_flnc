from uuid import UUID

from modules.assignments.repositories import assignments
from modules.assignments.services.student_views import StudentAssignment, student_assignments


def get_student_assignment(assignment_id: UUID, student_id: UUID) -> StudentAssignment:
    """One assignment the student is in; otherwise not found, even if it exists (A-02). No
    policy here: the caller is delivery's gate, which checks the student first."""
    record = assignments.get_record_for_student(assignment_id, student_id)
    return student_assignments([record], student_id)[0]
