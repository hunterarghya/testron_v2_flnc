"""Every delivery endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import StudentArea, TeacherArea
from modules.delivery.controllers import attempts, integrity, monitoring, my_tests, stages
from modules.delivery.dto.attempt_clock import AttemptClockOut, SaveAckOut, SubmitResultOut
from modules.delivery.dto.attempt_state import AttemptStateOut
from modules.delivery.dto.integrity import IntegrityAckOut
from modules.delivery.dto.monitor import AttemptSummaryOut, EndedOut, IntegrityEventOut, MonitorOut
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

# Student: sections and rapid fire (P-04, P-05)
router.add_api_operation(
    "/attempts/{attempt_id}/stages/next",
    ["POST"],
    stages.move_to_next_stage,
    response={200: AttemptStateOut},
    summary="Leave the current stage for the next one (safe to repeat)",
)
router.add_api_operation(
    "/attempts/{attempt_id}/stages/{stage_index}/return",
    ["POST"],
    stages.return_to_stage,
    response={200: AttemptStateOut},
    summary="Go back to a section left earlier, while its timer runs",
)

# Student: leaving the test (P-06); the event id comes from the browser, so retries are safe
router.add_api_operation(
    "/attempts/{attempt_id}/integrity-events/{event_id}",
    ["PUT"],
    integrity.report_integrity_event,
    response={200: IntegrityAckOut},
    summary="Report leaving the test; the server counts warnings and decides",
)

# Teacher: the live monitor and its actions (T-10, D-04)
router.add_api_operation(
    "/admin/assignments/{assignment_id}/monitor",
    ["GET"],
    monitoring.get_monitor,
    response={200: MonitorOut},
    auth=TeacherArea(),
    summary="Each student's sitting, live",
)
router.add_api_operation(
    "/admin/assignments/{assignment_id}/end",
    ["POST"],
    monitoring.end_for_everyone,
    response={200: EndedOut},
    auth=TeacherArea(),
    summary="End the test for everyone now (type END to confirm)",
)
router.add_api_operation(
    "/admin/attempts/{attempt_id}/force-submit",
    ["POST"],
    monitoring.force_submit_attempt,
    response={200: AttemptSummaryOut},
    auth=TeacherArea(),
    summary="End one student's sitting now",
)
router.add_api_operation(
    "/admin/attempts/{attempt_id}/integrity-events",
    ["GET"],
    monitoring.list_integrity_events,
    response={200: list[IntegrityEventOut]},
    auth=TeacherArea(),
    summary="Each time the student left the test",
)
router.add_api_operation(
    "/admin/attempts/{attempt_id}/override-disqualification",
    ["POST"],
    monitoring.override_disqualification,
    response={200: AttemptSummaryOut},
    auth=TeacherArea(),
    summary="Let a disqualified attempt count again",
)
