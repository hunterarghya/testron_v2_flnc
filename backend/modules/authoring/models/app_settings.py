from decimal import Decimal

from django.db import models

from core.clock import now
from modules.authoring.domain.values import IntegrityAction

_ACTIONS = [action.value for action in IntegrityAction]


class AppSettings(models.Model):
    """The one row of teacher defaults and branding (database_schema.md §3.4)."""

    id = models.SmallIntegerField(primary_key=True, default=1)
    coaching_name = models.TextField()
    # No logo is NULL, as database_schema.md §3.4 lists it
    logo_url = models.TextField(null=True)  # noqa: DJ001
    default_marks = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal(4))
    default_negative_marks = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal(1))
    default_integrity_grace_s = models.SmallIntegerField(default=5)
    default_integrity_max_warnings = models.SmallIntegerField(default=3)
    default_integrity_action = models.CharField(
        max_length=16, choices=[(action, action) for action in _ACTIONS]
    )
    updated_at = models.DateTimeField(default=now)

    class Meta:
        db_table = "app_settings"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            models.CheckConstraint(condition=models.Q(id=1), name="app_settings_single_row"),
            models.CheckConstraint(
                condition=models.Q(default_marks__gt=0), name="app_settings_marks_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(default_negative_marks__gte=0),
                name="app_settings_negative_marks_not_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(default_integrity_grace_s__range=(0, 60)),
                name="app_settings_grace_range",
            ),
            models.CheckConstraint(
                condition=models.Q(default_integrity_max_warnings__range=(1, 20)),
                name="app_settings_warnings_range",
            ),
            models.CheckConstraint(
                condition=models.Q(default_integrity_action__in=_ACTIONS),
                name="app_settings_action_valid",
            ),
        ]

    def __str__(self) -> str:
        return self.coaching_name
