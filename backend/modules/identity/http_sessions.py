"""The login session on a request: the identity steps that need HTTP.

Use cases decide who may log in; controllers then call these to set or clear the cookie.
Django rotates the session key on login, so a session id planted beforehand is useless.
"""

from datetime import timedelta
from uuid import UUID

from django.contrib.auth import login, logout, update_session_auth_hash
from django.http import HttpRequest

from core.context import Role
from modules.identity.repositories import users

# Accepts accounts that aren't active yet: pending students log in to see their status
BACKEND = "django.contrib.auth.backends.AllowAllUsersModelBackend"
# How long a session lasts without the app being opened (architecture.md §5.2)
SESSION_LIFETIME = {Role.TEACHER: timedelta(days=7), Role.STUDENT: timedelta(days=14)}


def start_session(request: HttpRequest, user_id: UUID) -> None:
    user = users.get_user(user_id)
    login(request, user, backend=BACKEND)
    request.session.set_expiry(SESSION_LIFETIME[Role(user.role)])


def renew_session(request: HttpRequest) -> None:
    """Restart the session's lifetime, so it only expires after that long unused."""
    account = session_account(request)
    if account is not None:
        request.session.set_expiry(SESSION_LIFETIME[account[1]])


def end_session(request: HttpRequest) -> None:
    logout(request)


def keep_session_after_password_change(request: HttpRequest) -> None:
    """Re-sign this session with the new password; the other devices stay logged out."""
    account = session_account(request)
    if account is not None:
        update_session_auth_hash(request, users.get_user(account[0]))


def session_account(request: HttpRequest) -> tuple[UUID, Role] | None:
    """Who is logged in on this request (Django already loaded the user), or None."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return None
    return user.pk, Role(getattr(user, "role", ""))
