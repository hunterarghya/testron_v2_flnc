"""Every students endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import SignedInArea, TeacherArea
from core.http.pagination import Page
from modules.students.controllers import admin_students, auth
from modules.students.dto.auth import SessionOut, SessionUserOut, SignUpAcceptedOut
from modules.students.dto.students import BulkResultOut, StudentRowOut

# Teacher area by default; the public admission routes (/auth/*) set auth=None (ADR-050)
router = Router(tags=["students"], auth=TeacherArea())

router.add_api_operation(
    "/auth/sign-up",
    ["POST"],
    auth.sign_up_with_password,
    auth=None,
    response={202: SignUpAcceptedOut},
    summary="Create a student account (unverified)",
    tags=["auth"],
)
router.add_api_operation(
    "/auth/email-verification",
    ["POST"],
    auth.verify_email,
    auth=None,
    response={200: SessionUserOut},
    summary="Verify the email with its code and log in",
    tags=["auth"],
)
router.add_api_operation(
    "/auth/login",
    ["POST"],
    auth.log_in_with_password,
    auth=None,
    response={200: SessionUserOut},
    summary="Log in with email and password",
    tags=["auth"],
)
router.add_api_operation(
    "/auth/session",
    ["GET"],
    auth.get_session,
    auth=None,
    response={200: SessionOut},
    summary="Who is logged in (or null) and the server time",
    tags=["auth"],
)
router.add_api_operation(
    "/auth/profile",
    ["PATCH"],
    auth.update_profile_name,
    auth=SignedInArea(),
    response={200: SessionUserOut},
    summary="Change your own name",
    tags=["auth"],
)

# Teacher: admission (T-14). Every route below inherits the router's TeacherArea.
router.add_api_operation(
    "/admin/students",
    ["GET"],
    admin_students.list_students,
    response={200: Page[StudentRowOut]},
    summary="One tab of the Students table",
)
router.add_api_operation(
    "/admin/students/approve",
    ["POST"],
    admin_students.approve_students,
    response={200: BulkResultOut},
    summary="Approve join requests",
)
router.add_api_operation(
    "/admin/students/decline",
    ["POST"],
    admin_students.decline_students,
    response={200: BulkResultOut},
    summary="Decline join requests (final)",
)
router.add_api_operation(
    "/admin/students/deactivate",
    ["POST"],
    admin_students.deactivate_students,
    response={200: BulkResultOut},
    summary="Deactivate students (ends their sessions)",
)
router.add_api_operation(
    "/admin/students/reactivate",
    ["POST"],
    admin_students.reactivate_students,
    response={200: BulkResultOut},
    summary="Reactivate students",
)
router.add_api_operation(
    "/admin/students/{student_id}/anonymize",
    ["POST"],
    admin_students.anonymize_student,
    response={204: None},
    summary="Delete a student permanently (keeps their results)",
)
