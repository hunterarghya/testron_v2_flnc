"""Every students endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import SignedInArea, TeacherArea
from core.http.bulk import BulkResultOut
from core.http.pagination import Page
from modules.students.controllers import admin_groups, admin_students, auth
from modules.students.dto.auth import SessionOut, SessionUserOut, SignUpAcceptedOut
from modules.students.dto.groups import AudienceCandidateOut, GroupDetailOut, GroupOut
from modules.students.dto.students import StudentDetailOut, StudentRowOut

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
    "/admin/students/{student_id}",
    ["GET"],
    admin_students.get_student,
    response={200: StudentDetailOut},
    summary="One student's page: details, groups and sharing",
)
router.add_api_operation(
    "/admin/students/{student_id}/anonymize",
    ["POST"],
    admin_students.anonymize_student,
    response={204: None},
    summary="Delete a student permanently (keeps their results)",
)

# Teacher: groups (T-16, T-17), the wizard's audience preview (T-07) and sharing (D-06)
router.add_api_operation(
    "/admin/groups",
    ["GET"],
    admin_groups.list_groups,
    response={200: list[GroupOut]},
    summary="Groups (active by default)",
)
router.add_api_operation(
    "/admin/groups",
    ["POST"],
    admin_groups.create_group,
    response={201: GroupOut},
    summary="Create a group",
)
router.add_api_operation(
    "/admin/groups/{group_id}",
    ["GET"],
    admin_groups.get_group,
    response={200: GroupDetailOut},
    summary="One group with its members",
)
router.add_api_operation(
    "/admin/groups/{group_id}",
    ["PATCH"],
    admin_groups.update_group,
    response={200: GroupOut},
    summary="Rename a group or change its description",
)
router.add_api_operation(
    "/admin/groups/{group_id}/archive",
    ["POST"],
    admin_groups.archive_group,
    response={200: GroupOut},
    summary="Archive a group",
)
router.add_api_operation(
    "/admin/groups/{group_id}/restore",
    ["POST"],
    admin_groups.restore_group,
    response={200: GroupOut},
    summary="Restore an archived group",
)
router.add_api_operation(
    "/admin/groups/{group_id}/members",
    ["POST"],
    admin_groups.add_group_members,
    response={200: BulkResultOut},
    summary="Add students to a group",
)
router.add_api_operation(
    "/admin/groups/{group_id}/members/remove",
    ["POST"],
    admin_groups.remove_group_members,
    response={200: BulkResultOut},
    summary="Remove students from a group",
)
router.add_api_operation(
    "/admin/audience-preview",
    ["GET"],
    admin_groups.preview_audience,
    response={200: list[AudienceCandidateOut]},
    summary="Active students in the chosen groups",
)
router.add_api_operation(
    "/admin/performance-shares",
    ["POST"],
    admin_groups.share_performance,
    response={200: BulkResultOut},
    summary="Share performance with students or a group",
)
router.add_api_operation(
    "/admin/performance-shares/remove",
    ["POST"],
    admin_groups.unshare_performance,
    response={200: BulkResultOut},
    summary="Stop sharing performance",
)
