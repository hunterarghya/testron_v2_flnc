from uuid import UUID

from modules.assignments.domain.answer_key import CorrectionRecord
from modules.assignments.repositories import papers


def list_answer_key_corrections(assignment_id: UUID) -> list[CorrectionRecord]:
    """The key's correction history (T-11, security.md T-05), newest first. No policy: the
    caller is results' teacher use case, which checks the teacher first."""
    return papers.corrections(assignment_id)
