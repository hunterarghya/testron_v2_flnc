"""`manage.py seed` (`just seed`): the data every installation starts with. Idempotent.

Today: the teacher account from TEACHER_EMAIL / TEACHER_NAME / TEACHER_INITIAL_PASSWORD.
The app settings row joins it with the authoring module (step 2.4).
"""

from typing import Any

from django.core.management.base import BaseCommand, CommandError

from core.config import get_settings
from core.context import system_ctx
from core.errors import DomainError
from modules.identity.public import seed_teacher


class Command(BaseCommand):
    help = "Create or update the teacher account from the environment (safe to repeat)."

    def handle(self, *args: Any, **options: Any) -> None:
        settings = get_settings()
        if not settings.teacher_email or not settings.teacher_name:
            raise CommandError("Set TEACHER_EMAIL and TEACHER_NAME first")
        password = settings.teacher_initial_password
        try:
            result = seed_teacher(
                system_ctx(),
                email=settings.teacher_email,
                name=settings.teacher_name,
                initial_password=password.get_secret_value() if password else None,
            )
        except DomainError as error:
            raise CommandError(f"{error.title}: {settings.teacher_email}") from None
        verb = "created" if result.created else "already existed, details updated"
        self.stdout.write(self.style.SUCCESS(f"Teacher {verb}: {settings.teacher_email}"))
