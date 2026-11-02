from dataclasses import dataclass
from uuid import UUID

from django.contrib.auth.hashers import make_password
from django.db import transaction

from core.context import Ctx
from core.emails import normalize_email
from core.text import clean_text_line
from modules.identity.domain.errors import TeacherEmailTaken
from modules.identity.repositories import users
from modules.identity.services.password_policy import ensure_password_strong


@dataclass(frozen=True, slots=True)
class SeedTeacherResult:
    user_id: UUID
    created: bool


def seed_teacher(
    ctx: Ctx, *, email: str, name: str, initial_password: str | None
) -> SeedTeacherResult:
    """Create the one teacher account from configuration, or bring it up to date
    (domain_model.md §3.1 #1, V1 F-19). Safe to run any number of times.

    The initial password is used only when the teacher is first created; later runs
    never touch it. Without one, the teacher logs in with Google or a password reset.
    The teacher's email can't be one a student already uses.
    """
    email = normalize_email(email)
    name = clean_text_line(name)
    with transaction.atomic():
        _ensure_email_free_for_teacher(email)
        teacher = users.find_teacher()
        if teacher is not None:
            users.update_teacher_details(teacher.id, email=email, name=name, now=ctx.now)
            return SeedTeacherResult(user_id=teacher.id, created=False)
        if initial_password is not None:
            ensure_password_strong(initial_password)
        user_id = users.insert_teacher(
            email=email, name=name, password_hash=make_password(initial_password), now=ctx.now
        )
    return SeedTeacherResult(user_id=user_id, created=True)


def _ensure_email_free_for_teacher(email: str) -> None:
    owner = users.find_user_by_email(email)
    if owner is not None and not owner.is_teacher:
        raise TeacherEmailTaken(context={"email": email})
