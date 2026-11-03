"""Who sits an assignment, and what was granted to whom (database_schema.md §3.5): the audience,
time extensions, retake grants, and who is waiting at the gate."""

from django.db import models
from django.db.models import Q

from core.clock import now
from core.db.base_model import UUIDModel
from modules.assignments.models.assignment import Assignment

# Students are named, not imported: the students module's models stay private to it
STUDENT = "students.Student"


class AudienceMember(models.Model):
    pk = models.CompositePrimaryKey("assignment_id", "student_id")
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="audience")
    student = models.ForeignKey(STUDENT, on_delete=models.RESTRICT, related_name="+")
    added_at = models.DateTimeField(default=now)

    class Meta:
        db_table = "audience_members"
        indexes = [  # noqa: RUF012  # Django's own class attribute
            # "My Tests", the hottest student query
            models.Index(fields=["student", "assignment"], name="audience_members_student"),
        ]

    def __str__(self) -> str:
        return f"{self.assignment_id}:{self.student_id}"


class Extension(UUIDModel):
    assignment = models.ForeignKey(Assignment, on_delete=models.RESTRICT, related_name="extensions")
    # Left empty when the extension is for everyone
    student = models.ForeignKey(STUDENT, on_delete=models.RESTRICT, related_name="+", null=True)
    # Left empty for the attempt's final stage
    stage_index = models.SmallIntegerField(null=True)
    seconds = models.IntegerField()
    created_at = models.DateTimeField(default=now)

    class Meta:
        db_table = "extensions"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            models.CheckConstraint(
                condition=Q(seconds__range=(1, 86_400)), name="extensions_seconds_range"
            ),
        ]
        indexes = [  # noqa: RUF012  # Django's own class attribute
            models.Index(fields=["assignment"], name="extensions_assignment"),
        ]

    def __str__(self) -> str:
        return f"+{self.seconds}s on {self.assignment_id}"


class RetakeGrant(UUIDModel):
    assignment = models.ForeignKey(Assignment, on_delete=models.RESTRICT, related_name="+")
    student = models.ForeignKey(STUDENT, on_delete=models.RESTRICT, related_name="+")
    granted_at = models.DateTimeField(default=now)
    # The attempt that used it. Named, not imported: delivery sits above assignments (ADR-074)
    consumed_by_attempt = models.OneToOneField(
        "delivery.Attempt", on_delete=models.RESTRICT, related_name="+", null=True
    )

    class Meta:
        db_table = "retake_grants"
        indexes = [  # noqa: RUF012  # Django's own class attribute
            # The oldest unused grant (domain_model.md §3.6)
            models.Index(
                fields=["assignment", "student", "granted_at"],
                condition=Q(consumed_by_attempt__isnull=True),
                name="retake_grants_open",
            ),
        ]

    def __str__(self) -> str:
        return f"retake {self.student_id} on {self.assignment_id}"


class LobbyPresence(models.Model):
    pk = models.CompositePrimaryKey("assignment_id", "student_id")
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="+")
    student = models.ForeignKey(STUDENT, on_delete=models.CASCADE, related_name="+")
    last_seen_at = models.DateTimeField()

    class Meta:
        db_table = "lobby_presence"

    def __str__(self) -> str:
        return f"{self.student_id} at {self.assignment_id}"
