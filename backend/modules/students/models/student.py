from django.conf import settings
from django.db import models

from core.context import StudentStatus

_STATUSES = [status.value for status in StudentStatus]


class Student(models.Model):
    """A student's admission status; the account itself lives in identity (database_schema §3.2).

    The user is referenced by the swappable AUTH_USER_MODEL name, so this module never
    imports identity's models.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, primary_key=True, on_delete=models.RESTRICT, related_name="+"
    )
    status = models.CharField(max_length=16, choices=[(s, s) for s in _STATUSES])
    # When the account became PENDING: the order of the teacher's Pending tab
    requested_at = models.DateTimeField(null=True)
    decided_at = models.DateTimeField(null=True)
    deactivated_at = models.DateTimeField(null=True)
    anonymized_at = models.DateTimeField(null=True)
    anonymized_number = models.PositiveIntegerField(null=True, unique=True)

    class Meta:
        db_table = "students"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            models.CheckConstraint(
                condition=models.Q(status__in=_STATUSES), name="students_status_valid"
            ),
            # "Deleted student #n" needs both, and only anonymized students have them
            models.CheckConstraint(
                condition=(
                    models.Q(
                        status=StudentStatus.ANONYMIZED,
                        anonymized_at__isnull=False,
                        anonymized_number__isnull=False,
                    )
                    | (
                        ~models.Q(status=StudentStatus.ANONYMIZED)
                        & models.Q(anonymized_at__isnull=True, anonymized_number__isnull=True)
                    )
                ),
                name="students_anonymized_consistent",
            ),
        ]
        indexes = [  # noqa: RUF012  # Django's own class attribute
            models.Index(fields=["status", "requested_at"], name="students_status_requested"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} ({self.status})"
