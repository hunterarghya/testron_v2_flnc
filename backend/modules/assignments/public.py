"""The only names other modules may import from assignments (R-08)."""

from modules.assignments.domain.entry import Entry
from modules.assignments.domain.paper_summary import PaperSummary, Stage
from modules.assignments.services.commands.touch_lobby_presence import touch_lobby_presence
from modules.assignments.services.queries.get_student_assignment import get_student_assignment
from modules.assignments.services.queries.list_student_assignments import (
    list_student_assignments,
)
from modules.assignments.services.student_views import StudentAssignment

__all__ = [
    "Entry",
    "PaperSummary",
    "Stage",
    "StudentAssignment",
    "get_student_assignment",
    "list_student_assignments",
    "touch_lobby_presence",
]
