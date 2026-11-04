from datetime import datetime

from django.db import connection, transaction

# Takes the run only if the last one is old enough; the row is born on the first run.
# Two requests at once: the row lock lets exactly one of them through.
_CLAIM = """
INSERT INTO housekeeping_runs AS run (id, last_run_at) VALUES (1, %(now)s)
ON CONFLICT (id) DO UPDATE SET last_run_at = excluded.last_run_at
WHERE run.last_run_at <= %(due_after)s
RETURNING id
"""


def claim(*, now: datetime, due_after: datetime) -> bool:
    """True if this caller gets to run housekeeping now."""
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(_CLAIM, {"now": now, "due_after": due_after})
        return cursor.fetchone() is not None
