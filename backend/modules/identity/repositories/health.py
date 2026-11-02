from django.db import connection


def ping_database() -> None:
    """Run `SELECT 1`. Raises the driver's error if the database doesn't answer."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
