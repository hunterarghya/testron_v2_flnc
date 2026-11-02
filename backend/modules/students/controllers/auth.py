from django.http import HttpRequest
from ninja import Status

from core.http.client_ip import client_ip
from core.http.context import ctx_from
from modules.identity.public import start_session
from modules.students.dto.auth import SessionUserOut, SignUpAcceptedOut, SignUpIn, VerifyEmailIn
from modules.students.services.commands import sign_up_with_password as sign_up
from modules.students.services.commands import verify_email as verification


def sign_up_with_password(request: HttpRequest, payload: SignUpIn) -> Status[SignUpAcceptedOut]:
    result = sign_up.sign_up_with_password(
        ctx_from(request),
        name=payload.name,
        email=payload.email,
        password=payload.password,
        client_ip=client_ip(request),
    )
    return Status(202, SignUpAcceptedOut.from_result(result))


def verify_email(request: HttpRequest, payload: VerifyEmailIn) -> SessionUserOut:
    user = verification.verify_email(
        ctx_from(request), email=payload.email, code=payload.code, client_ip=client_ip(request)
    )
    start_session(request, user.id)
    return SessionUserOut.from_view(user)
