"""What the assignment use cases need to know about attempts: who has started, and how far
everyone has got. The attempts table arrives in Phase 5a (build_phases.md 5a.1); until then
no attempt can exist, so these answer "none" (backlog B-17)."""

from collections.abc import Sequence
from uuid import UUID

from modules.assignments.domain.assignment import Progress


def students_with_attempts(assignment_id: UUID) -> set[UUID]:
    del assignment_id
    return set()


def progress_by_assignment(assignment_ids: Sequence[UUID]) -> dict[UUID, Progress]:
    return {assignment_id: Progress() for assignment_id in assignment_ids}
