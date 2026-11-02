from django.db import models

from core.clock import now
from core.db.base_model import TimestampedModel
from modules.students.models.student import Student

MAX_GROUP_NAME_LENGTH = 80
MAX_GROUP_DESCRIPTION_LENGTH = 500


class Group(TimestampedModel):
    """A class or batch the teacher picks students by (database_schema.md §3.2)."""

    name = models.CharField(max_length=MAX_GROUP_NAME_LENGTH)
    # Case- and space-insensitive form of the name, for uniqueness among active groups
    normalized_name = models.CharField(max_length=MAX_GROUP_NAME_LENGTH)
    description = models.CharField(max_length=MAX_GROUP_DESCRIPTION_LENGTH, default="", blank=True)
    archived_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "groups"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            models.CheckConstraint(condition=~models.Q(name=""), name="groups_name_not_empty"),
            models.UniqueConstraint(
                fields=["normalized_name"],
                condition=models.Q(archived_at__isnull=True),
                name="groups_active_name",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class GroupMembership(models.Model):
    pk = models.CompositePrimaryKey("group_id", "student_id")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="memberships")
    added_at = models.DateTimeField(default=now)

    class Meta:
        db_table = "group_memberships"
        indexes = [  # noqa: RUF012  # Django's own class attribute
            # A student's groups
            models.Index(fields=["student"], name="group_memberships_student"),
        ]

    def __str__(self) -> str:
        return f"{self.group_id}:{self.student_id}"
