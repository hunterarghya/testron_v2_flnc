"""Every delivery endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import StudentArea
from modules.delivery.controllers import my_tests
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
