from django.http import HttpRequest
from ninja import Status

from core.http.context import ctx_from
from modules.identity.dto.verification import ResendVerificationIn
from modules.identity.services.commands import resend_verification as command


def resend_verification(request: HttpRequest, payload: ResendVerificationIn) -> Status[None]:
    command.resend_verification(ctx_from(request), email=payload.email)
    return Status(202, None)
