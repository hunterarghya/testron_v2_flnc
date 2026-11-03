from django.db import models
from django.db.models import Q
from django.db.models.functions import Length
from django.db.models.lookups import Range

from core.db.base_model import TimestampedModel
from modules.authoring.domain.values import IntegrityAction, TimingKind

_TIMINGS = [kind.value for kind in TimingKind]
_ACTIONS = [action.value for action in IntegrityAction]
MAX_TITLE_LENGTH = 200


class Test(TimestampedModel):
    """A test the teacher writes, with its settings as columns (database_schema.md §3.4)."""

    title = models.TextField(default="Untitled test")
    instructions = models.JSONField(null=True)
    timing_kind = models.CharField(max_length=16, choices=[(kind, kind) for kind in _TIMINGS])
    duration_s = models.IntegerField(null=True)
    default_question_s = models.IntegerField(null=True)
    allow_return = models.BooleanField(default=False)
    shuffle_questions = models.BooleanField(default=False)
    shuffle_options = models.BooleanField(default=False)
    marks = models.DecimalField(max_digits=7, decimal_places=2)
    negative_marks = models.DecimalField(max_digits=7, decimal_places=2)
    integrity_grace_s = models.SmallIntegerField()
    integrity_max_warnings = models.SmallIntegerField()
    integrity_action = models.CharField(max_length=16, choices=[(a, a) for a in _ACTIONS])
    # Optimistic concurrency: every change adds one (domain_model.md §3.4)
    revision = models.IntegerField(default=1)
    archived_at = models.DateTimeField(null=True)
    last_assigned_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "tests"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            models.CheckConstraint(
                condition=Range(Length("title"), (1, MAX_TITLE_LENGTH)), name="tests_title_length"
            ),
            models.CheckConstraint(
                condition=Q(timing_kind__in=_TIMINGS), name="tests_timing_valid"
            ),
            # The duration belongs to TOTAL, the per-question default to PER_QUESTION
            models.CheckConstraint(
                condition=(Q(timing_kind="TOTAL", duration_s__isnull=False, duration_s__gte=60))
                | (~Q(timing_kind="TOTAL") & Q(duration_s__isnull=True)),
                name="tests_duration_iff_total",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        timing_kind="PER_QUESTION",
                        default_question_s__isnull=False,
                        default_question_s__gte=5,
                    )
                )
                | (~Q(timing_kind="PER_QUESTION") & Q(default_question_s__isnull=True)),
                name="tests_question_time_iff_per_question",
            ),
            models.CheckConstraint(condition=Q(marks__gt=0), name="tests_marks_positive"),
            models.CheckConstraint(
                condition=Q(negative_marks__gte=0), name="tests_negative_marks_not_negative"
            ),
            models.CheckConstraint(
                condition=Q(integrity_grace_s__range=(0, 60)), name="tests_grace_range"
            ),
            models.CheckConstraint(
                condition=Q(integrity_max_warnings__range=(1, 20)), name="tests_warnings_range"
            ),
            models.CheckConstraint(
                condition=Q(integrity_action__in=_ACTIONS), name="tests_action_valid"
            ),
        ]
        indexes = [  # noqa: RUF012  # Django's own class attribute
            # The library: active tests, most recently changed first
            models.Index(fields=["archived_at", "-updated_at"], name="tests_library"),
        ]

    def __str__(self) -> str:
        return self.title
