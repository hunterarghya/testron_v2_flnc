"""Every assignments endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import TeacherArea
from core.http.bulk import BulkResultOut
from core.http.pagination import Page
from modules.assignments.controllers import admin_assignments as admin
from modules.assignments.controllers import admin_lobby as lobby
from modules.assignments.dto.lobby import ActivationOut, LobbyOut
from modules.assignments.dto.views import AssignmentDetailOut, AssignmentRowOut, PasswordOut

router = Router(tags=["assignments"], auth=TeacherArea())

# Teacher: the list (T-06), the wizard (T-07) and the overview (T-08)
router.add_api_operation(
    "/admin/assignments",
    ["GET"],
    admin.list_assignments,
    response={200: Page[AssignmentRowOut]},
    summary="One tab of the assignments list",
)
router.add_api_operation(
    "/admin/assignments",
    ["POST"],
    admin.create_assignment,
    response={201: AssignmentDetailOut},
    summary="Assign a test (freezes the paper)",
)
router.add_api_operation(
    "/admin/assignments/{assignment_id}",
    ["GET"],
    admin.get_assignment,
    response={200: AssignmentDetailOut},
    summary="One assignment's overview",
)
router.add_api_operation(
    "/admin/assignments/{assignment_id}",
    ["PATCH"],
    admin.update_assignment,
    response={200: AssignmentDetailOut},
    summary="Change an assignment's settings",
)
router.add_api_operation(
    "/admin/assignments/{assignment_id}/audience",
    ["PUT"],
    admin.replace_audience,
    response={200: AssignmentDetailOut},
    summary="Replace the audience (before the start only)",
)
router.add_api_operation(
    "/admin/assignments/{assignment_id}/audience/add",
    ["POST"],
    admin.add_audience,
    response={200: BulkResultOut},
    summary="Add students to the audience",
)
router.add_api_operation(
    "/admin/assignments/{assignment_id}/audience/remove",
    ["POST"],
    admin.remove_audience,
    response={200: BulkResultOut},
    summary="Remove students who haven't begun",
)
router.add_api_operation(
    "/admin/assignments/{assignment_id}/password",
    ["PUT"],
    admin.set_password,
    response={204: None},
    summary="Set, change or remove the test password",
)
router.add_api_operation(
    "/admin/assignments/{assignment_id}/password",
    ["GET"],
    admin.reveal_password,
    response={200: PasswordOut},
    summary="Reveal the test password (audited)",
)
router.add_api_operation(
    "/admin/assignments/{assignment_id}/cancel",
    ["POST"],
    admin.cancel_assignment,
    response={204: None},
    summary="Cancel an assignment no one has begun",
)

# Teacher: Start and the lobby (T-09)
router.add_api_operation(
    "/admin/assignments/{assignment_id}/activate",
    ["POST"],
    lobby.activate_assignment,
    response={200: ActivationOut},
    summary="Start the test for everyone (idempotent)",
)
router.add_api_operation(
    "/admin/assignments/{assignment_id}/lobby",
    ["GET"],
    lobby.get_lobby,
    response={200: LobbyOut},
    summary="Who has the gate open now",
)
