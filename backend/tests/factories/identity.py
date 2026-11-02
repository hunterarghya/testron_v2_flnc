from typing import cast

import factory

from core.context import Role
from modules.identity.models import User


class UserFactory(factory.django.DjangoModelFactory[User]):
    """A verified, active student by default. `teacher=True` for the teacher."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"student{n}@example.com")
    name = factory.Sequence(lambda n: f"Student {n}")
    role = Role.STUDENT
    is_active = True
    password = factory.django.Password("correct-horse-battery")

    class Params:
        teacher = factory.Trait(role=Role.TEACHER, email="teacher@example.com", name="Teacher")


def make_user(**fields: object) -> User:
    """A saved user, typed for tests (factory_boy itself is untyped)."""
    return cast(User, UserFactory(**fields))
