from django.conf import settings
from django.db import models

from core.clock import now
from core.db.base_model import UUIDModel


class AuditEntry(UUIDModel):
    """One sensitive action, kept for good (database_schema.md §3.8). Append-only: a trigger
    refuses changes and deletions (migration 0002)."""

    # Empty for the system itself (e.g. lazy finalization); kept if the person is later deleted
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    # Dotted, e.g. `assignment.reveal_password`
    action = models.TextField()
    target_type = models.TextField()
    target_id = models.UUIDField()
    data = models.JSONField(default=dict)
    at = models.DateTimeField(default=now)

    class Meta:
        db_table = "audit_entries"
        indexes = [  # noqa: RUF012  # Django's own class attribute
            models.Index(fields=["target_type", "target_id", "-at"], name="audit_entries_target"),
            models.Index(fields=["-at"], name="audit_entries_at"),
        ]

    def __str__(self) -> str:
        return f"{self.action} on {self.target_type} {self.target_id}"
