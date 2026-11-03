from django.db import models
from django.db.models import Q
from django.db.models.functions import Length
from django.db.models.lookups import Range

from core.db.base_model import TimestampedModel
from modules.assignments.domain.values import PublicationMode, PublishContent, WindowKind

_WINDOWS = [kind.value for kind in WindowKind]
_MODES = [mode.value for mode in PublicationMode]
_CONTENTS = [content.value for content in PublishContent]
_ACTIONS = ["AUTO_SUBMIT", "DISQUALIFY"]
_TIMINGS = ["TOTAL", "PER_QUESTION", "SECTIONED"]
MAX_TITLE_LENGTH = 200

# Each window has exactly its own fields (database_schema.md §3.5, assignments_window_shape)
_NO_WINDOW_TIMES = Q(starts_at__isnull=True, opens_at__isnull=True, closes_at__isnull=True)
WINDOW_SHAPE = (
    (Q(window_kind="MANUAL") & _NO_WINDOW_TIMES)
    | Q(
        window_kind="SCHEDULED",
        starts_at__isnull=False,
        planned_at__isnull=True,
        opens_at__isnull=True,
        closes_at__isnull=True,
    )
    | (
        Q(
            window_kind="DEADLINE",
            opens_at__isnull=False,
            closes_at__isnull=False,
            closes_at__gt=models.F("opens_at"),
        )
        & Q(starts_at__isnull=True, planned_at__isnull=True, late_entry_s__isnull=True)
    )
    | (Q(window_kind="OPEN", planned_at__isnull=True, late_entry_s__isnull=True) & _NO_WINDOW_TIMES)
)


class Assignment(TimestampedModel):
    """A test given to chosen students in a window, with its own gate, integrity and
    publication settings (domain_model.md §3.5). Its paper never changes."""

    test = models.ForeignKey("authoring.Test", on_delete=models.RESTRICT, related_name="+")
    title = models.TextField()
    window_kind = models.CharField(max_length=16, choices=[(k, k) for k in _WINDOWS])
    planned_at = models.DateTimeField(null=True)
    starts_at = models.DateTimeField(null=True)
    opens_at = models.DateTimeField(null=True)
    closes_at = models.DateTimeField(null=True)
    late_entry_s = models.IntegerField(null=True)
    requires_activation = models.BooleanField()
    # Fernet ciphertext with ASSIGNMENT_PASSWORD_KEY; the teacher can reveal it (ADR-018)
    password_ciphertext = models.TextField(null=True)  # noqa: DJ001  # null = no password (database_schema.md §3.5)
    timing_kind = models.CharField(max_length=16, choices=[(k, k) for k in _TIMINGS])
    total_duration_s = models.IntegerField()
    integrity_grace_s = models.SmallIntegerField()
    integrity_max_warnings = models.SmallIntegerField()
    integrity_action = models.CharField(max_length=16, choices=[(a, a) for a in _ACTIONS])
    publication_mode = models.CharField(max_length=16, choices=[(m, m) for m in _MODES])
    publication_delay_s = models.IntegerField(null=True)
    publish_content = models.CharField(max_length=16, choices=[(c, c) for c in _CONTENTS])
    show_paper = models.BooleanField()
    show_solutions = models.BooleanField()
    show_rank_and_stats = models.BooleanField()
    activated_at = models.DateTimeField(null=True)
    ended_at = models.DateTimeField(null=True)
    cancelled_at = models.DateTimeField(null=True)
    published_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "assignments"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            models.CheckConstraint(
                condition=Range(Length("title"), (1, MAX_TITLE_LENGTH)),
                name="assignments_title_length",
            ),
            models.CheckConstraint(
                condition=Q(window_kind__in=_WINDOWS), name="assignments_window_kind_valid"
            ),
            models.CheckConstraint(condition=WINDOW_SHAPE, name="assignments_window_shape"),
            models.CheckConstraint(
                condition=Q(late_entry_s__isnull=True) | Q(late_entry_s__gte=0),
                name="assignments_late_entry_min",
            ),
            models.CheckConstraint(
                condition=Q(total_duration_s__gt=0), name="assignments_duration_positive"
            ),
            models.CheckConstraint(
                condition=Q(integrity_grace_s__range=(0, 60)), name="assignments_grace_range"
            ),
            models.CheckConstraint(
                condition=Q(integrity_max_warnings__range=(1, 20)),
                name="assignments_warnings_range",
            ),
            models.CheckConstraint(
                condition=Q(integrity_action__in=_ACTIONS), name="assignments_action_valid"
            ),
            models.CheckConstraint(
                condition=Q(timing_kind__in=_TIMINGS), name="assignments_timing_valid"
            ),
            models.CheckConstraint(
                condition=Q(publication_mode__in=_MODES), name="assignments_publication_mode_valid"
            ),
            models.CheckConstraint(
                condition=Q(publish_content__in=_CONTENTS), name="assignments_publish_content_valid"
            ),
            # A delay belongs to AUTO_DELAYED, and only there
            models.CheckConstraint(
                condition=Q(
                    publication_mode="AUTO_DELAYED",
                    publication_delay_s__isnull=False,
                    publication_delay_s__gt=0,
                )
                | (~Q(publication_mode="AUTO_DELAYED") & Q(publication_delay_s__isnull=True)),
                name="assignments_delay_iff_delayed",
            ),
            # Once started it can't be cancelled
            models.CheckConstraint(
                condition=~Q(cancelled_at__isnull=False, activated_at__isnull=False),
                name="assignments_not_cancelled_after_activation",
            ),
        ]
        indexes = [  # noqa: RUF012  # Django's own class attribute
            models.Index(fields=["-created_at"], name="assignments_created"),
            models.Index(
                fields=["starts_at"],
                condition=Q(cancelled_at__isnull=True),
                name="assignments_starts",
            ),
            models.Index(
                fields=["opens_at"],
                condition=Q(cancelled_at__isnull=True),
                name="assignments_opens",
            ),
            models.Index(fields=["test"], name="assignments_test"),
        ]

    def __str__(self) -> str:
        return self.title
