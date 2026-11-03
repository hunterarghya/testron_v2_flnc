from collections.abc import Sequence
from uuid import UUID

from core.context import StudentStatus
from modules.identity.models import User
from modules.students.models import Group, GroupMembership, Student
from tests.factories.identity import make_user


def make_student(status: StudentStatus = StudentStatus.ACTIVE, **user_fields: object) -> User:
    """A student account with its admission row. Unverified ones have no verified email."""
    user_fields.setdefault("is_active", status is StudentStatus.ACTIVE)
    if status is StudentStatus.UNVERIFIED:
        user_fields.setdefault("email_verified_at", None)
    user = make_user(**user_fields)
    Student.objects.create(user_id=user.id, status=status)
    return user


def make_group(name: str, members: Sequence[UUID] = ()) -> Group:
    group = Group.objects.create(name=name, normalized_name=name.casefold())
    GroupMembership.objects.bulk_create(
        [GroupMembership(group=group, student_id=sid) for sid in members]
    )
    return group
