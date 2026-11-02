"""The Content-Security-Policy (architecture.md §5.15).

Scripts stay strict ('self' only, no 'unsafe-inline'). The built SPA has two small inline
scripts (the import map and Nuxt's config); they are allowed by their exact SHA-256 hash,
read from the built HTML, so any other inline script is still blocked.
"""

import base64
import hashlib
import re
from functools import cache
from pathlib import Path

_POLICY: dict[str, tuple[str, ...]] = {
    "default-src": ("'self'",),
    "img-src": ("'self'", "https://ik.imagekit.io", "data:"),
    "connect-src": ("'self'", "https://upload.imagekit.io"),
    "font-src": ("'self'", "data:"),
    # The UI library and KaTeX set styles inline; scripts never get this exception
    "style-src": ("'self'", "'unsafe-inline'"),
    "script-src": ("'self'",),
    "frame-ancestors": ("'none'",),
    "base-uri": ("'self'",),
    "form-action": ("'self'", "https://accounts.google.com"),
}
# An inline <script> with code in it (not src=, not a JSON data block)
_INLINE_SCRIPT = re.compile(
    r"<script(?![^>]*\bsrc=)(?![^>]*type=\"application/json\")[^>]*>(.*?)</script>", re.DOTALL
)


def content_security_policy(spa_build_dir: Path | None) -> str:
    hashes = spa_script_hashes(str(spa_build_dir)) if spa_build_dir else ()
    directives = dict(_POLICY, **{"script-src": (*_POLICY["script-src"], *hashes)})
    return "; ".join(f"{name} {' '.join(sources)}" for name, sources in directives.items())


def inline_script_hashes(html: str) -> list[str]:
    """CSP hash sources for every inline script in one HTML page."""
    return [_hash_source(body) for body in _INLINE_SCRIPT.findall(html) if body.strip()]


@cache
def spa_script_hashes(spa_build_dir: str) -> tuple[str, ...]:
    """The hashes across every page of the build, read once per process (a deploy restarts)."""
    pages = sorted(Path(spa_build_dir).rglob("*.html"))
    found = {source for page in pages for source in inline_script_hashes(page.read_text("utf-8"))}
    return tuple(sorted(found))


def _hash_source(script: str) -> str:
    digest = hashlib.sha256(script.encode("utf-8")).digest()
    return f"'sha256-{base64.b64encode(digest).decode('ascii')}'"
