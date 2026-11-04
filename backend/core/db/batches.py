"""Bounded deletes for housekeeping (database_schema.md §5.4): a request that does cleanup
must stay fast, so each table gives up at most a batch of rows per run."""

from typing import Any

from django.db.models import QuerySet


def delete_first(rows: QuerySet[Any], limit: int) -> int:
    """Delete at most `limit` of these rows; returns how many went. Django's delete() can't
    take a LIMIT, so the keys are picked first (two queries)."""
    keys = list(rows.values_list("pk", flat=True)[:limit])
    if not keys:
        return 0
    deleted, _ = rows.model.objects.filter(pk__in=keys).delete()
    return int(deleted)
