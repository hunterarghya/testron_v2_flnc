from django.db import models


class HousekeepingRun(models.Model):
    """When housekeeping last ran: one row, claimed by the first request after ten minutes
    (database_schema.md §5.4; ADR-083)."""

    id = models.SmallIntegerField(primary_key=True, default=1)
    last_run_at = models.DateTimeField()

    class Meta:
        db_table = "housekeeping_runs"
        constraints = [  # noqa: RUF012  # Django's own class attribute
            models.CheckConstraint(condition=models.Q(id=1), name="housekeeping_runs_single_row"),
        ]

    def __str__(self) -> str:
        return f"Housekeeping last ran at {self.last_run_at}"
