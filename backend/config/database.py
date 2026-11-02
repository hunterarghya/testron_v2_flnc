"""Turn the database URLs into Django's DATABASES setting (database_schema.md §7)."""

from urllib.parse import parse_qsl, unquote, urlsplit


def database_settings(url: str, *, direct_url: str | None) -> dict[str, dict[str, object]]:
    """`default` goes through Neon's pooler; `direct` is the same database without it.

    Migrations run with `migrate --database=direct`, because schema changes need a
    real session that the pooler can't give.
    """
    direct = _connection(direct_url or url)
    direct["TEST"] = {"MIRROR": "default"}  # tests use one database for both names
    return {"default": _connection(url), "direct": direct}


def _connection(url: str) -> dict[str, object]:
    parts = urlsplit(url)
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parts.path.removeprefix("/")),
        "USER": unquote(parts.username or ""),
        "PASSWORD": unquote(parts.password or ""),
        "HOST": parts.hostname or "",
        "PORT": str(parts.port or ""),
        # The pooler hands each transaction a different connection, so nothing may
        # outlive one: no kept-open connections, server-side cursors or prepared statements
        "CONN_MAX_AGE": 0,
        "DISABLE_SERVER_SIDE_CURSORS": True,
        # Each use case opens its own transaction (architecture.md §5.7)
        "ATOMIC_REQUESTS": False,
        # Query options such as sslmode=require are passed through to the driver
        "OPTIONS": {"prepare_threshold": None, **dict(parse_qsl(parts.query))},
    }
