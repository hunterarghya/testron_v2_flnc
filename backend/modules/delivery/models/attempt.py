from django.db import models
from django.db.models import F, Q

from core.db.base_model import UUIDModel
from modules.delivery.domain.values import AttemptStatus, EndReason

_STATUSES = [status.value for status in AttemptStatus]
_REASONS = [reason.value for reason in EndReason]

# Ended and graded happen together, in one transaction (domain_model.md §5.5)
END_SHAPE = Q(
    status=AttemptStatus.IN_PROGRESS.value,
    ended_at__isnull=True,
    end_reason__isnull=True,
    graded_at__isnull=True,
    score__isnull=True,
) | Q(
    status=AttemptStatus.ENDED.value,
    ended_at__isnull=False,
    end_reason__isnull=False,
    graded_at__isnull=False,
    score__isnull=False,
    answer_key_version__isnull=False,
)


class Attempt(UUIDModel):
    """One sitting of an assignment by one student (domain_model.md §3.6)."""

    # Named, not imported: other modules' models stay private to them
    assignment = models.ForeignKey(
        "assignments.Assignment", on_delete=models.RESTRICT, related_name="+"
    )
    student = models.ForeignKey("students.Student", on_delete=models.RESTRICT, related_name="+")
    take_number = models.SmallIntegerField()
    # A retake, or a late first sitting: its own clock (§5.7)
    is_granted = models.BooleanField()
    status = models.CharField(max_length=16, choices=[(s, s) for s in _STATUSES])
    end_reason = models.CharField(  # noqa: DJ001  # null while in progress (database_schema.md §3.6)
        max_length=16, choices=[(r, r) for r in _REASONS], null=True
    )
    started_at = models.DateTimeField()
    # The instant its clock is measured from (§5.1)
    anchor_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True)
    seed = models.BigIntegerField()
    # Stage list, question and option order: fixed at start (database_schema.md §4.4)
    plan = models.JSONField()
    current_stage_index = models.SmallIntegerField(default=0)
    furthest_stage_index = models.SmallIntegerField(default=0)
    warning_count = models.SmallIntegerField(default=0)
    last_seen_at = models.DateTimeField()
    # The exam client allowed to write: the latest device wins (§5.9)
    active_client_id = models.UUIDField(null=True)
    disqualification_overridden_at = models.DateTimeField(null=True)
    score = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    max_score = models.DecimalField(max_digits=8, decimal_places=2)
    graded_at = models.DateTimeField(null=True)
    answer_key_version = models.IntegerField(null=True)

    class Meta:
        db_table = "attempts"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            models.UniqueConstraint(
                fields=["assignment", "student", "take_number"], name="attempts_take_unique"
            ),
            # E-01: at most one sitting in progress per student and assignment
            models.UniqueConstraint(
                fields=["assignment", "student"],
                condition=Q(status=AttemptStatus.IN_PROGRESS.value),
                name="attempts_one_in_progress",
            ),
            models.CheckConstraint(condition=Q(take_number__gte=1), name="attempts_take_min"),
            models.CheckConstraint(condition=Q(status__in=_STATUSES), name="attempts_status_valid"),
            models.CheckConstraint(
                condition=Q(end_reason__isnull=True) | Q(end_reason__in=_REASONS),
                name="attempts_end_reason_valid",
            ),
            models.CheckConstraint(condition=END_SHAPE, name="attempts_end_shape"),
            models.CheckConstraint(
                condition=Q(ended_at__isnull=True) | Q(ended_at__gte=F("started_at")),
                name="attempts_ended_after_start",
            ),
            models.CheckConstraint(
                condition=Q(furthest_stage_index__gte=F("current_stage_index"))
                & Q(current_stage_index__gte=0),
                name="attempts_stage_pointers",
            ),
            models.CheckConstraint(
                condition=Q(warning_count__gte=0), name="attempts_warning_count_min"
            ),
            models.CheckConstraint(
                condition=Q(disqualification_overridden_at__isnull=True)
                | Q(end_reason=EndReason.DISQUALIFIED.value),
                name="attempts_override_only_disqualified",
            ),
        ]
        indexes = [  # noqa: RUF012  # Django's own class attribute
            # The monitor, lazy finalization, the gradebook
            models.Index(fields=["assignment", "status"], name="attempts_assignment_status"),
            # Past Tests
            models.Index(fields=["student", "-started_at"], name="attempts_student_started"),
            # The housekeeping sweep
            models.Index(
                fields=["status", "anchor_at"],
                condition=Q(status=AttemptStatus.IN_PROGRESS.value),
                name="attempts_in_progress_anchor",
            ),
        ]

    def __str__(self) -> str:
        return f"take {self.take_number} of {self.assignment_id} by {self.student_id}"
