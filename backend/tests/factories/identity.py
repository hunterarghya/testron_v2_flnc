from typing import cast

import factory

from core import clock
from core.context import Role
from modules.identity.models import User


class UserFactory(factory.django.DjangoModelFactory[User]):
    """A verified, active student by default. Traits: `teacher=True`, `google_only=True`."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"student{n}@example.com")
    name = factory.Sequence(lambda n: f"Student {n}")
    role = Role.STUDENT
    is_active = True
    email_verified_at = factory.LazyFunction(clock.now)
    password = factory.django.Password("correct-horse-battery")

    class Params:
        teacher = factory.Trait(role=Role.TEACHER, email="teacher@example.com", name="Teacher")
        # Signed up with Google and never set a password
        google_only = factory.Trait(
            password=factory.django.Password(None),
            google_sub=factory.Sequence(lambda n: f"google-sub-{n}"),
        )


def make_user(**fields: object) -> User:
    """A saved user, typed for tests (factory_boy itself is untyped)."""
    return cast(User, UserFactory(**fields))


# Tests outside identity name the user type through here, not through identity's models
__all__ = ["User", "UserFactory", "make_user"]
