"""Starting a login session on a request: the one identity step that needs HTTP.

Use cases decide who may log in; the controller then calls this to set the cookie.
Django rotates the session key here, so a session id planted before login is useless.
"""

from uuid import UUID

from django.contrib.auth import login
from django.http import HttpRequest

from modules.identity.repositories import users

# Accepts accounts that aren't active yet: pending students log in to see their status
BACKEND = "django.contrib.auth.backends.AllowAllUsersModelBackend"


def start_session(request: HttpRequest, user_id: UUID) -> None:
    login(request, users.get_user(user_id), backend=BACKEND)
