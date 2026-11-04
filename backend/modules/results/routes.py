"""Every results endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import StudentArea, TeacherArea
from core.http.pagination import Page
from modules.results.controllers import badges, corrections, performance, results
from modules.results.dto.answer_sheet import AnswerSheetOut
from modules.results.dto.badges import BadgesOut
from modules.results.dto.corrections import KeyCorrectedOut, KeyCorrectionOut
from modules.results.dto.dashboard import DashboardOut, ResultsInboxRowOut
from modules.results.dto.gradebook import GradebookOut, KeyedPaperOut, QuestionStatOut
from modules.results.dto.past_tests import PastTestOut
from modules.results.dto.performance import GroupPerformanceOut, PerformanceOut
from modules.results.dto.result import ResultOut

# Teacher area by default; the student /my/* routes set auth=StudentArea()
router = Router(tags=["results"], auth=TeacherArea())

router.add_api_operation(
    "/admin/badges",
    ["GET"],
    badges.get_badges,
    response={200: BadgesOut},
    summary="The counts on the teacher's menu",
)

# Teacher: answer key corrections (D-05)
router.add_api_operation(
    "/admin/assignments/{assignment_id}/answer-key-corrections",
    ["POST"],
    corrections.correct_answer_key,
    response={200: KeyCorrectedOut},
    summary="Correct one question's answer and regrade everyone",
)
router.add_api_operation(
    "/admin/assignments/{assignment_id}/answer-key-corrections",
    ["GET"],
    corrections.list_key_corrections,
    response={200: list[KeyCorrectionOut]},
    summary="Every answer key correction, newest first, with what changed and why",
)

# Teacher: results (T-01, T-11, T-12, T-13); student: P-08, P-09
router.add_api_operation(
    "/admin/assignments/{assignment_id}/gradebook",
    ["GET"],
    results.get_gradebook,
    response={200: GradebookOut},
    summary="Every student's result, ranked, absent ones included",
)
router.add_api_operation(
    "/admin/assignments/{assignment_id}/question-stats",
    ["GET"],
    results.get_question_stats,
    response={200: list[QuestionStatOut]},
    summary="How each question went",
)
router.add_api_operation(
    "/admin/assignments/{assignment_id}/answer-key",
    ["GET"],
    results.get_answer_key,
    response={200: KeyedPaperOut},
    summary="The paper with its answers and solutions",
)
router.add_api_operation(
    "/admin/attempts/{attempt_id}/sheet",
    ["GET"],
    results.get_answer_sheet,
    response={200: AnswerSheetOut},
    summary="One attempt with everything (T-12)",
)
router.add_api_operation(
    "/admin/assignments/{assignment_id}/answer-sheets",
    ["GET"],
    results.list_answer_sheets,
    response={200: list[AnswerSheetOut]},
    summary="Answer sheets for the browser to export",
)
router.add_api_operation(
    "/admin/assignments/{assignment_id}/exports/gradebook.csv",
    ["GET"],
    results.export_gradebook_csv,
    summary="The gradebook as a CSV download",
)
router.add_api_operation(
    "/admin/results",
    ["GET"],
    results.list_results_inbox,
    response={200: Page[ResultsInboxRowOut]},
    summary="Closed tests and their publication (T-13)",
)
router.add_api_operation(
    "/admin/dashboard",
    ["GET"],
    results.get_dashboard,
    response={200: DashboardOut},
    summary="Live, upcoming and recent tests, and what needs attention",
)
router.add_api_operation(
    "/my/past-tests",
    ["GET"],
    results.list_my_past_tests,
    response={200: Page[PastTestOut]},
    auth=StudentArea(),
    summary="The student's ended takes and missed tests",
)
router.add_api_operation(
    "/my/results/{attempt_id}",
    ["GET"],
    results.get_my_result,
    response={200: ResultOut},
    auth=StudentArea(),
    summary="One result, as far as it is published",
)

# Performance reports: P-10, T-15 and T-17
router.add_api_operation(
    "/admin/students/{student_id}/performance",
    ["GET"],
    performance.get_student_performance,
    response={200: PerformanceOut},
    summary="One student's chapters and topics, weakest first, and their trend",
)
router.add_api_operation(
    "/admin/groups/{group_id}/performance",
    ["GET"],
    performance.get_group_performance,
    response={200: GroupPerformanceOut},
    summary="A group's weak chapters and each test's score over time",
)
router.add_api_operation(
    "/my/performance",
    ["GET"],
    performance.get_my_performance,
    response={200: PerformanceOut},
    auth=StudentArea(),
    summary="The student's own report, while the teacher shares it",
)
