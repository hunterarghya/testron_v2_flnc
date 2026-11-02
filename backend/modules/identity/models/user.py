from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower

from core.context import Role
from core.db.base_model import TimestampedModel

MAX_EMAIL_LENGTH = 254
MAX_NAME_LENGTH = 120


class UserManager(BaseUserManager["User"]):
    """Lookups only. Users are created by identity's services, never through this manager."""


class User(AbstractBaseUser, TimestampedModel):
    """A person who can log in: the one teacher or a student (database_schema.md §3.1).

    There are no Django staff or superuser columns: the back office is for the teacher only,
    so those are derived from the role.
    """

    email = models.CharField(max_length=MAX_EMAIL_LENGTH, unique=True)
    name = models.CharField(max_length=MAX_NAME_LENGTH)
    role = models.CharField(max_length=16, choices=[(role.value, role.value) for role in Role])
    google_sub = models.CharField(max_length=255, null=True, unique=True)  # noqa: DJ001  # null = no Google link (many allowed)
    email_verified_at = models.DateTimeField(null=True)
    # Django's login gate, kept equal to "student is ACTIVE" (database_schema.md §5.3)
    is_active = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["name"]  # noqa: RUF012  # Django's own class attribute

    class Meta:
        db_table = "users"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            models.CheckConstraint(
                condition=models.Q(email=Lower("email")), name="users_email_lower"
            ),
            models.CheckConstraint(condition=~models.Q(name=""), name="users_name_not_empty"),
            models.CheckConstraint(
                condition=models.Q(role__in=[role.value for role in Role]), name="users_role_valid"
            ),
            # Exactly one teacher can exist (domain_model.md §3.1 #1)
            models.UniqueConstraint(
                fields=["role"], condition=models.Q(role=Role.TEACHER), name="users_one_teacher"
            ),
        ]

    def __str__(self) -> str:
        return self.email

    @property
    def is_teacher(self) -> bool:
        return self.role == Role.TEACHER

    # The back office (Django admin) asks these; only the teacher may use it
    @property
    def is_staff(self) -> bool:
        return self.is_active and self.is_teacher

    def has_perm(self, perm: str, obj: object = None) -> bool:
        return self.is_staff

    def has_module_perms(self, app_label: str) -> bool:
        return self.is_staff
