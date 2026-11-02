"""Named row locks for repositories (database_schema.md §5.1).

Each lock covers only the queried table's rows (`of=("self",)`), never the rows of
joined tables, and must be taken inside the use case's transaction.
"""

from django.db.models import Model, QuerySet


def for_update[M: Model](queryset: QuerySet[M]) -> QuerySet[M]:
    """Exclusive: the row is about to change state (submit, end, grade)."""
    return queryset.select_for_update(of=("self",))


def for_share[M: Model](queryset: QuerySet[M]) -> QuerySet[M]:
    """Keep the row from changing state while dependent rows are written (e.g. a save).

    Django has no FOR SHARE, so this takes FOR NO KEY UPDATE (ADR-043): it still waits
    for FOR UPDATE holders, but two holders of the same row also wait for each other.
    """
    return queryset.select_for_update(no_key=True, of=("self",))


def skip_locked[M: Model](queryset: QuerySet[M]) -> QuerySet[M]:
    """Exclusive, skipping rows someone else holds (lazy finalization, housekeeping)."""
    return queryset.select_for_update(skip_locked=True, of=("self",))
