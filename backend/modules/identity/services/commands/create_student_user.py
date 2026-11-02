from uuid import UUID

from django.contrib.auth.hashers import make_password

from core.context import Ctx
from core.text import clean_text_line
from modules.identity.repositories import users
from modules.identity.services.password_policy import ensure_password_strong


def create_student_user(ctx: Ctx, *, email: str, name: str, password: str) -> UUID:
    """Create the login account for a new student (domain_model.md §3.1 #2).

    Sign-up always creates a STUDENT, never the teacher. The account stays inactive
    until the teacher approves it. `email` is already normalized. Raises PasswordTooWeak,
    or EmailTaken when another sign-up won the race for the same address.
    """
    ensure_password_strong(password)
    return users.insert_student_user(
        email=email,
        name=clean_text_line(name),
        password_hash=make_password(password),
        now=ctx.now,
    )
