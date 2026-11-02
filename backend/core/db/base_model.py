"""Base classes for every table: a time-ordered UUID key and creation/update times."""

from django.db import models

from core.clock import now
from core.ids import uuid7


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)

    class Meta:
        abstract = True


class TimestampedModel(UUIDModel):
    """Times come from `core.clock`, so tests control them.

    Repositories set `updated_at` themselves in every update: there is no logic in `save()`.
    """

    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(default=now)

    class Meta:
        abstract = True
