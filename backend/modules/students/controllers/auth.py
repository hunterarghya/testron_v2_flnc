from django.http import HttpRequest
from ninja import Status

from core.http.client_ip import client_ip
from core.http.context import ctx_from
from modules.identity.public import renew_session, start_session
from modules.students.dto.auth import (
    LoginIn,
    ProfileIn,
    SessionOut,
    SessionUserOut,
    SignUpAcceptedOut,
    SignUpIn,
    VerifyEmailIn,
)
from modules.students.services.commands import log_in_with_password as log_in
from modules.students.services.commands import sign_up_with_password as sign_up
from modules.students.services.commands import update_profile_name as profile
from modules.students.services.commands import verify_email as verification
from modules.students.services.queries import get_session as session


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


def log_in_with_password(request: HttpRequest, payload: LoginIn) -> SessionUserOut:
    user = log_in.log_in_with_password(
        ctx_from(request),
        email=payload.email,
        password=payload.password,
        client_ip=client_ip(request),
    )
    start_session(request, user.id)
    return SessionUserOut.from_view(user)


def get_session(request: HttpRequest) -> SessionOut:
    # Each app load keeps an active user's session alive (sliding lifetime)
    renew_session(request)
    return SessionOut.from_view(session.get_session(ctx_from(request)))


def update_profile_name(request: HttpRequest, payload: ProfileIn) -> SessionUserOut:
    return SessionUserOut.from_view(
        profile.update_profile_name(ctx_from(request), name=payload.name)
    )
