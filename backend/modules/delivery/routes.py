"""Every delivery endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import StudentArea
from modules.delivery.controllers import attempts, my_tests
from modules.delivery.dto.attempt_clock import AttemptClockOut, SaveAckOut, SubmitResultOut
from modules.delivery.dto.attempt_state import AttemptStateOut
from modules.delivery.dto.my_tests import GateStateOut, MyTestsOut

# Student area by default; the teacher monitor routes set auth=TeacherArea()
router = Router(tags=["delivery"], auth=StudentArea())

# Student: My Tests (P-01) and the gate (P-02)
router.add_api_operation(
    "/my/tests",
    ["GET"],
    my_tests.list_my_tests,
    response={200: MyTestsOut},
    summary="The student's tests to start, join or resume, and upcoming ones",
)
router.add_api_operation(
    "/my/tests/{assignment_id}/gate",
    ["GET"],
    my_tests.get_gate_state,
    response={200: GateStateOut},
    summary="The gate: rules and whether the student may begin (also the lobby heartbeat)",
)

# Student: the exam hall (P-03, P-07); writes carry X-Exam-Client (latest device wins)
router.add_api_operation(
    "/my/tests/{assignment_id}/attempts",
    ["POST"],
    attempts.start_attempt,
    response={200: AttemptStateOut, 201: AttemptStateOut},
    summary="Start a sitting (201), or resume the one in progress (200)",
)
router.add_api_operation(
    "/attempts/{attempt_id}",
    ["GET"],
    attempts.get_attempt_state,
    response={200: AttemptStateOut},
    summary="The attempt as the hall shows it, on load and resume",
)
router.add_api_operation(
    "/attempts/{attempt_id}/responses/{question_id}",
    ["PUT"],
    attempts.save_response,
    response={200: SaveAckOut},
    summary="Save one answer (an older client_seq is acknowledged and ignored)",
)
router.add_api_operation(
    "/attempts/{attempt_id}/questions/{question_id}/visit",
    ["POST"],
    attempts.record_visit,
    response={204: None},
    summary="Mark a question as seen",
)
router.add_api_operation(
    "/attempts/{attempt_id}/heartbeat",
    ["POST"],
    attempts.heartbeat_attempt,
    response={200: AttemptClockOut},
    summary="The hall's heartbeat: the current clock",
)
router.add_api_operation(
    "/attempts/{attempt_id}/submit",
    ["POST"],
    attempts.submit_attempt,
    response={200: SubmitResultOut},
    summary="Submit the attempt (safe to repeat)",
)
