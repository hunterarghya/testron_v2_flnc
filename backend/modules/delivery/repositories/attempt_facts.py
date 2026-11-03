"""What the student has done with each assignment: an attempt in progress, attempts made.
The attempts table arrives in Phase 5a (build_phases.md 5a.1); until then no attempt can
exist (backlog B-17)."""

from collections.abc import Sequence
from uuid import UUID

from modules.delivery.domain.gate import Sittings


def sittings_by_assignment(
    student_id: UUID, assignment_ids: Sequence[UUID]
) -> dict[UUID, Sittings]:
    del student_id
    return {assignment_id: Sittings() for assignment_id in assignment_ids}
