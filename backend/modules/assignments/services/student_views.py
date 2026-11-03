"""An assignment as one student's gate and test list need it (P-01, P-02): when they may
enter, and what the paper is like. Built here for list_student_assignments and
get_student_assignment."""

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from modules.assignments.domain.assignment import AssignmentRecord
from modules.assignments.domain.entry import Entry, entry_window, is_locked
from modules.assignments.domain.paper_summary import PaperSummary, paper_summary
from modules.assignments.domain.settings import Integrity
from modules.assignments.domain.window import Window
from modules.assignments.repositories import extensions, papers, retake_grants


@dataclass(frozen=True, slots=True)
class StudentAssignment:
    assignment_id: UUID
    title: str
    window: Window
    entry: Entry
    has_password: bool
    # Students wait for Start or need a password
    locked: bool
    paper: PaperSummary
    integrity: Integrity
    # A retake grant (or a late first sitting) not used yet (domain_model.md §5.7)
    has_unused_grant: bool


def student_assignments(
    records: Sequence[AssignmentRecord], student_id: UUID
) -> list[StudentAssignment]:
    """Three queries, however many assignments there are."""
    ids = [record.id for record in records]
    contents = papers.contents(ids)
    grants = extensions.grants_by_assignment(ids)
    granted = retake_grants.with_unused_grant(student_id, ids)
    return [
        StudentAssignment(
            assignment_id=record.id,
            title=record.settings.title,
            window=record.settings.window,
            entry=entry_window(record.timeline, grants.get(record.id, [])),
            has_password=record.has_password,
            locked=is_locked(record.timeline, has_password=record.has_password),
            paper=paper_summary(contents[record.id]),
            integrity=record.settings.integrity,
            has_unused_grant=record.id in granted,
        )
        for record in records
    ]
