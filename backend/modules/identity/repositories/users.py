from datetime import datetime
from uuid import UUID

from django.db import IntegrityError, transaction

from core.context import Role
from core.errors import NotFound
from modules.identity.domain.errors import EmailTaken
from modules.identity.models import User


def get_user(user_id: UUID) -> User:
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise NotFound("user") from None


def find_user_id_by_email(email: str) -> UUID | None:
    """The id of the account with this (normalized) email, or None when there is none."""
    return User.objects.filter(email=email).values_list("id", flat=True).first()


def insert_student_user(*, email: str, name: str, password_hash: str, now: datetime) -> UUID:
    """A new student account: not active until the teacher approves it."""
    user = User(
        email=email,
        name=name,
        role=Role.STUDENT,
        password=password_hash,
        is_active=False,
        created_at=now,
        updated_at=now,
    )
    try:
        # A savepoint, so a lost race leaves the caller's transaction usable
        with transaction.atomic():
            user.save(force_insert=True)
    except IntegrityError:
        raise EmailTaken() from None
    return user.id


def mark_email_verified(user_id: UUID, *, now: datetime) -> None:
    User.objects.filter(pk=user_id, email_verified_at__isnull=True).update(
        email_verified_at=now, updated_at=now
    )
