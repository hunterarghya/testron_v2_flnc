from core.errors import DomainError


class DatabaseUnavailable(DomainError):
    """The deep health check couldn't reach the database."""

    code = "database_unavailable"
    status = 503
    title = "The database is not reachable"
