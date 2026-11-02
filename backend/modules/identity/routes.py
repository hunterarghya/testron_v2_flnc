"""Every identity endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from core.http.areas import SignedInArea
from modules.identity.controllers import health, password, session, verification
from modules.identity.dto.health import HealthOut

# Mostly public (/healthz, /auth/*); signed-in routes set auth=SignedInArea()
router = Router(tags=["auth"])

router.add_api_operation(
    "/healthz",
    ["GET"],
    health.get_health,
    response={200: HealthOut},
    summary="Liveness and server time",
)
router.add_api_operation(
    "/auth/csrf",
    ["GET"],
    session.get_csrf_cookie,
    response={204: None},
    summary="Set the CSRF cookie",
)
router.add_api_operation(
    "/auth/email-verification/resend",
    ["POST"],
    verification.resend_verification,
    response={202: None},
    summary="Email a new verification code",
)
router.add_api_operation(
    "/auth/logout",
    ["POST"],
    session.log_out,
    auth=SignedInArea(),
    response={204: None},
    summary="Log out of this device",
)
router.add_api_operation(
    "/auth/password-reset",
    ["POST"],
    password.request_password_reset,
    response={202: None},
    summary="Email a password reset code",
)
router.add_api_operation(
    "/auth/password-reset/confirm",
    ["POST"],
    password.confirm_password_reset,
    response={204: None},
    summary="Set a new password with the code (ends every session)",
)
router.add_api_operation(
    "/auth/password",
    ["POST"],
    password.change_password,
    auth=SignedInArea(),
    response={204: None},
    summary="Change your own password",
)
