"""What happens inside an attempt (database_schema.md §3.6): each stage's times, each saved
answer, and each time the student left the test."""

from django.db import models
from django.db.models import F, Q

from modules.delivery.domain.values import IntegrityKind
from modules.delivery.models.attempt import Attempt

_KINDS = [kind.value for kind in IntegrityKind]


class StageProgress(models.Model):
    pk = models.CompositePrimaryKey("attempt_id", "stage_index")
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="+")
    stage_index = models.SmallIntegerField()
    # The first entry only (domain_model.md §5.3)
    entered_at = models.DateTimeField(null=True)
    left_at = models.DateTimeField(null=True)
    closed_at = models.DateTimeField(null=True)
    # A late joiner arrived after this stage's boundary
    missed = models.BooleanField(default=False)

    class Meta:
        db_table = "stage_progress"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            models.CheckConstraint(
                condition=Q(stage_index__gte=0), name="stage_progress_index_min"
            ),
            models.CheckConstraint(
                condition=~Q(missed=True, entered_at__isnull=False),
                name="stage_progress_missed_never_entered",
            ),
            models.CheckConstraint(
                condition=Q(closed_at__isnull=True)
                | Q(entered_at__isnull=True)
                | Q(closed_at__gte=F("entered_at")),
                name="stage_progress_closed_after_entry",
            ),
        ]

    def __str__(self) -> str:
        return f"stage {self.stage_index} of {self.attempt_id}"


class Response(models.Model):
    pk = models.CompositePrimaryKey("attempt_id", "question_id")
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="+")
    # A paper question id: the paper is JSON, so the service checks it against the plan
    question_id = models.UUIDField()
    # Null: cleared, or never answered (database_schema.md §4.5)
    answer = models.JSONField(null=True)
    marked_for_review = models.BooleanField(default=False)
    first_visited_at = models.DateTimeField(null=True)
    client_seq = models.BigIntegerField()
    saved_at = models.DateTimeField()

    class Meta:
        db_table = "responses"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            models.CheckConstraint(condition=Q(client_seq__gte=0), name="responses_client_seq_min"),
        ]

    def __str__(self) -> str:
        return f"{self.question_id} in {self.attempt_id}"


class IntegrityEvent(models.Model):
    # Made by the client, so a retried report is the same event (E-20)
    id = models.UUIDField(primary_key=True)
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="+")
    kind = models.CharField(max_length=16, choices=[(k, k) for k in _KINDS])
    # Client time, corrected by the client's offset from the server
    left_at = models.DateTimeField()
    returned_at = models.DateTimeField(null=True)
    counted = models.BooleanField(default=False)
    reported_at = models.DateTimeField()

    class Meta:
        db_table = "integrity_events"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            models.CheckConstraint(
                condition=Q(kind__in=_KINDS), name="integrity_events_kind_valid"
            ),
            models.CheckConstraint(
                condition=~Q(kind=IntegrityKind.DEVICE_CHANGED.value, counted=True),
                name="integrity_events_device_change_not_counted",
            ),
        ]
        indexes = [  # noqa: RUF012  # Django's own class attribute
            models.Index(fields=["attempt", "left_at"], name="integrity_events_attempt"),
        ]

    def __str__(self) -> str:
        return f"{self.kind} in {self.attempt_id}"
