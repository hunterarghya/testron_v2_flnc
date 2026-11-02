from django.db import models


class RateLimitBucket(models.Model):
    """One fixed-window counter per key (database_schema.md §3.1).

    Read and written only by `core.rate_limit` with a single SQL upsert; this model
    exists so the table has a migration.
    """

    key = models.CharField(max_length=255, primary_key=True)
    window_started_at = models.DateTimeField()
    hits = models.PositiveIntegerField()
    blocked_until = models.DateTimeField(null=True)

    class Meta:
        db_table = "rate_limit_buckets"

    def __str__(self) -> str:
        return self.key
