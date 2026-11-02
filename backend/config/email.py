"""Turn EMAIL_URL (smtp://, smtp+tls://, smtp+ssl://) into Django's email settings."""

from dataclasses import dataclass
from urllib.parse import unquote, urlsplit

_DEFAULT_SMTP_PORT = 25


@dataclass(frozen=True, slots=True)
class EmailServer:
    host: str = "localhost"
    port: int = _DEFAULT_SMTP_PORT
    user: str = ""
    password: str = ""
    use_tls: bool = False
    use_ssl: bool = False


def parse_email_url(url: str | None) -> EmailServer:
    """The SMTP server to send through. No URL (tests, image build) means nothing is sent."""
    if url is None:
        return EmailServer()
    parts = urlsplit(url)
    return EmailServer(
        host=parts.hostname or "localhost",
        port=parts.port or _DEFAULT_SMTP_PORT,
        user=unquote(parts.username or ""),
        password=unquote(parts.password or ""),
        use_tls=parts.scheme == "smtp+tls",
        use_ssl=parts.scheme == "smtp+ssl",
    )
