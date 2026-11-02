from django.http import HttpRequest
from ninja import Status

from core.http.client_ip import client_ip
from core.http.context import ctx_from
from modules.identity.dto.password import ChangePasswordIn, PasswordResetConfirmIn, PasswordResetIn
from modules.identity.http_sessions import keep_session_after_password_change
from modules.identity.services.commands import change_password as change
from modules.identity.services.commands import confirm_password_reset as confirm
from modules.identity.services.commands import request_password_reset as reset


def request_password_reset(request: HttpRequest, payload: PasswordResetIn) -> Status[None]:
    reset.request_password_reset(ctx_from(request), email=payload.email)
    return Status(202, None)


def confirm_password_reset(request: HttpRequest, payload: PasswordResetConfirmIn) -> Status[None]:
    confirm.confirm_password_reset(
        ctx_from(request),
        email=payload.email,
        code=payload.code,
        new_password=payload.new_password,
        client_ip=client_ip(request),
    )
    return Status(204, None)


def change_password(request: HttpRequest, payload: ChangePasswordIn) -> Status[None]:
    change.change_password(
        ctx_from(request),
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    keep_session_after_password_change(request)
    return Status(204, None)
