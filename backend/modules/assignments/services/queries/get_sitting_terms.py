from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.assignments.domain.lifecycle import ExtensionGrant
from modules.assignments.domain.settings import Integrity
from modules.assignments.domain.window import Window
from modules.assignments.repositories import assignments, extensions


@dataclass(frozen=True, slots=True)
class SittingTerms:
    """What an attempt's clock and rules depend on, as of now (domain_model.md §5.2)."""

    title: str
    window: Window
    # The teacher ended it for everyone
    ended_at: datetime | None
    # Extra time for everyone and for this student
    extensions: tuple[ExtensionGrant, ...]
    integrity: Integrity


def get_sitting_terms(assignment_id: UUID, student_id: UUID) -> SittingTerms:
    """For the exam hall's every request, in two queries. No policy: the caller is delivery,
    which has found the student's own attempt first."""
    record = assignments.get_record_for_student(assignment_id, student_id)
    grants = extensions.grants_for_student([assignment_id], student_id)
    return SittingTerms(
        title=record.settings.title,
        window=record.settings.window,
        ended_at=record.timeline.ended_at,
        extensions=tuple(grants.get(assignment_id, [])),
        integrity=record.settings.integrity,
    )
