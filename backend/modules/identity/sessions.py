"""The session engine (`SESSION_ENGINE`): Django's database sessions, plus the user id.

Django stores the logged-in user inside the session data; copying it into its own
column is what makes "log this user out everywhere" possible.
"""

from typing import Any
from uuid import UUID

from django.contrib.auth import SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore as DatabaseSessionStore

from modules.identity.models.session import UserSession


class SessionStore(DatabaseSessionStore):
    @classmethod
    def get_model_class(cls) -> type[UserSession]:
        return UserSession

    def create_model_instance(self, data: dict[str, Any]) -> UserSession:
        session = super().create_model_instance(data)
        if not isinstance(session, UserSession):
            raise TypeError("the session engine must build UserSession rows")
        user_id = data.get(SESSION_KEY)
        session.user_id = UUID(str(user_id)) if user_id else None
        return session
