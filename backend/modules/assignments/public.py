"""The only names other modules may import from assignments (R-08)."""

from modules.assignments.domain.entry import Entry
from modules.assignments.domain.lifecycle import ExtensionGrant
from modules.assignments.domain.paper_summary import PaperSummary, Stage
from modules.assignments.domain.settings import Integrity
from modules.assignments.domain.values import WindowKind
from modules.assignments.domain.window import Window
from modules.assignments.services.commands.consume_retake_grant import consume_retake_grant
from modules.assignments.services.commands.touch_lobby_presence import touch_lobby_presence
from modules.assignments.services.queries.get_answer_key import AnswerKeyView, get_answer_key
from modules.assignments.services.queries.get_paper_content import get_paper_content
from modules.assignments.services.queries.get_sitting_terms import SittingTerms, get_sitting_terms
from modules.assignments.services.queries.get_student_assignment import get_student_assignment
from modules.assignments.services.queries.is_password_correct import is_password_correct
from modules.assignments.services.queries.list_student_assignments import (
    list_student_assignments,
)
from modules.assignments.services.student_views import StudentAssignment

__all__ = [
    "AnswerKeyView",
    "Entry",
    "ExtensionGrant",
    "Integrity",
    "PaperSummary",
    "SittingTerms",
    "Stage",
    "StudentAssignment",
    "Window",
    "WindowKind",
    "consume_retake_grant",
    "get_answer_key",
    "get_paper_content",
    "get_sitting_terms",
    "get_student_assignment",
    "is_password_correct",
    "list_student_assignments",
    "touch_lobby_presence",
]
