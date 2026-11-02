"""Every students endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import SignedInArea, TeacherArea
from modules.students.controllers import auth
from modules.students.dto.auth import SessionOut, SessionUserOut, SignUpAcceptedOut

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
