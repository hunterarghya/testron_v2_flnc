"""Cache headers for the SPA files WhiteNoise serves (ADR-086)."""


def revalidate_html(headers: dict[str, str], path: str, url: str) -> None:
    """Pages are checked with the server on every load, so right after a release no browser
    keeps an old page pointing at script files that are gone. Hashed /_nuxt/ files stay
    cached for a year (WHITENOISE_IMMUTABLE_FILE_TEST)."""
    if path.endswith(".html"):
        headers["Cache-Control"] = "no-cache"
