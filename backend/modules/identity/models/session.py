from django.contrib.sessions.base_session import AbstractBaseSession
from django.db import models


class UserSession(AbstractBaseSession):
    """Django's session row plus the user it belongs to.

    The indexed user id lets a password reset or a deactivation end every session of
    one user in a single DELETE (database_schema.md §3.1).
    """

    user_id = models.UUIDField(null=True, db_index=True)

    class Meta:
        db_table = "django_session"
