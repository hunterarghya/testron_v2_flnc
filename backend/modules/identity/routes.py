"""Every identity endpoint: path + method -> controller (ADR-030). No logic here."""

from ninja import Router

from modules.identity.controllers import health, verification
from modules.identity.dto.health import HealthOut

# Mostly public (/healthz, /app, /auth/*); signed-in routes set auth=SignedInArea()
router = Router(tags=["auth"])

router.add_api_operation(
    "/healthz",
    ["GET"],
    health.get_health,
    response={200: HealthOut},
    summary="Liveness and server time",
)
router.add_api_operation(
    "/auth/email-verification/resend",
    ["POST"],
    verification.resend_verification,
    response={202: None},
    summary="Email a new verification code",
)
