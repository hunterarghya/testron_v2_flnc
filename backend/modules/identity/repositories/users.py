from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from django.contrib.auth.hashers import make_password
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


def find_user_by_email(email: str) -> User | None:
    """The account with this (normalized) email, or None when there is none."""
    return User.objects.filter(email=email).first()


def set_password_hash(user_id: UUID, password_hash: str, *, now: datetime) -> None:
    User.objects.filter(pk=user_id).update(password=password_hash, updated_at=now)


def set_name(user_id: UUID, name: str, *, now: datetime) -> None:
    User.objects.filter(pk=user_id).update(name=name, updated_at=now)


def find_teacher() -> User | None:
    return User.objects.filter(role=Role.TEACHER).first()


def insert_teacher(*, email: str, name: str, password_hash: str, now: datetime) -> UUID:
    teacher = User.objects.create(
        email=email,
        name=name,
        role=Role.TEACHER,
        password=password_hash,
        is_active=True,
        email_verified_at=now,
        created_at=now,
        updated_at=now,
    )
    return teacher.id


def update_teacher_details(user_id: UUID, *, email: str, name: str, now: datetime) -> None:
    User.objects.filter(pk=user_id).update(email=email, name=name, updated_at=now)


def set_active(user_ids: Sequence[UUID], *, active: bool, now: datetime) -> None:
    User.objects.filter(pk__in=user_ids).update(is_active=active, updated_at=now)


def scrub(user_id: UUID, *, name: str, email: str, now: datetime) -> None:
    """Remove everything that identifies the person and every way to log in."""
    User.objects.filter(pk=user_id).update(
        name=name,
        email=email,
        password=make_password(None),
        google_sub=None,
        is_active=False,
        updated_at=now,
    )
