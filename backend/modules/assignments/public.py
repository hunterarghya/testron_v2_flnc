"""The only names other modules may import from assignments (R-08)."""

from modules.assignments.domain.answer_key import CorrectionRecord, KeyEntry
from modules.assignments.domain.entry import Entry
from modules.assignments.domain.lifecycle import ExtensionGrant
from modules.assignments.domain.paper_summary import PaperSummary, Stage
from modules.assignments.domain.settings import Integrity, Publication
from modules.assignments.domain.values import WindowKind
from modules.assignments.domain.window import Window
from modules.assignments.services.commands.consume_retake_grant import consume_retake_grant
from modules.assignments.services.commands.correct_answer_key_entry import (
    correct_answer_key_entry,
)
from modules.assignments.services.commands.delete_stale_lobby_presence import (
    delete_stale_lobby_presence,
)
from modules.assignments.services.commands.mark_assignment_ended import mark_assignment_ended
from modules.assignments.services.commands.touch_lobby_presence import touch_lobby_presence
from modules.assignments.services.queries.get_answer_key import AnswerKeyView, get_answer_key
from modules.assignments.services.queries.get_monitor_frame import (
    MonitorFrame,
    MonitorMember,
    get_monitor_frame,
)
from modules.assignments.services.queries.get_paper_content import get_paper_content
from modules.assignments.services.queries.get_results_frame import (
    KeyedPaper,
    ResultsFrame,
    get_keyed_paper,
    get_results_frame,
    get_results_frame_for_student,
    list_results_frames_for_student,
)
from modules.assignments.services.queries.get_sitting_terms import SittingTerms, get_sitting_terms
from modules.assignments.services.queries.get_student_assignment import get_student_assignment
from modules.assignments.services.queries.is_password_correct import is_password_correct
from modules.assignments.services.queries.list_answer_key_corrections import (
    list_answer_key_corrections,
)
from modules.assignments.services.queries.list_assignment_titles import list_assignment_titles
from modules.assignments.services.queries.list_assignments import (
    AssignmentFilter,
    Tab,
    list_assignments,
)
from modules.assignments.services.queries.list_student_assignments import (
    list_student_assignments,
)
from modules.assignments.services.student_views import StudentAssignment
from modules.assignments.services.views import AssignmentRow

__all__ = [
    "AnswerKeyView",
    "AssignmentFilter",
    "AssignmentRow",
    "CorrectionRecord",
    "Entry",
    "ExtensionGrant",
    "Integrity",
    "KeyEntry",
    "KeyedPaper",
    "MonitorFrame",
    "MonitorMember",
    "PaperSummary",
    "Publication",
    "ResultsFrame",
    "SittingTerms",
    "Stage",
    "StudentAssignment",
    "Tab",
    "Window",
    "WindowKind",
    "consume_retake_grant",
    "correct_answer_key_entry",
    "delete_stale_lobby_presence",
    "get_answer_key",
    "get_keyed_paper",
    "get_monitor_frame",
    "get_paper_content",
    "get_results_frame",
    "get_results_frame_for_student",
    "get_sitting_terms",
    "get_student_assignment",
    "is_password_correct",
    "list_answer_key_corrections",
    "list_assignment_titles",
    "list_assignments",
    "list_results_frames_for_student",
    "list_student_assignments",
    "mark_assignment_ended",
    "touch_lobby_presence",
]
