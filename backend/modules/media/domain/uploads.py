"""What may be uploaded, where it goes, and which image addresses content may use
(editor_content_spec.md §2.3 and §5.1, security.md §4)."""

from datetime import datetime, timedelta

from core.errors import FieldError, FieldsInvalid

# Type -> the file extension stored for it. No SVG: it can carry scripts.
IMAGE_TYPES = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/gif": "gif"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
SIGNATURE_LIFETIME = timedelta(minutes=10)
MAX_URL_LENGTH = 2048
# The file's first bytes for each type; the browser's own claim isn't trusted
_MAGIC = (
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
)
_WEBP = (b"RIFF", b"WEBP")
_FORBIDDEN_IN_URL = ("?", "#", "\\", "..")


def ensure_upload_allowed(mime: str, size_bytes: int) -> None:
    """Checked before signing, so an SVG or a 50 MB photo is refused up front."""
    errors = []
    if mime not in IMAGE_TYPES:
        errors.append(FieldError("mime", "unsupported_type", "Use a PNG, JPEG, WebP or GIF image"))
    if size_bytes > MAX_UPLOAD_BYTES:
        errors.append(FieldError("size_bytes", "too_large", "Use an image of 5 MB or less"))
    if errors:
        raise FieldsInvalid(*errors)


def upload_folder(root: str, now: datetime) -> str:
    """One folder per month (`/tests/2026/11`), so no folder grows without end."""
    return f"{root}/{now:%Y/%m}"


def is_url_under(url: str, prefix: str) -> bool:
    """True for a plain file address inside `prefix`: no query, fragment or way out of it.

    Sizes are added when the image is shown (`?tr=…`), never stored (editor_content_spec §5.2).
    """
    if len(url) > MAX_URL_LENGTH or not url.startswith(prefix) or len(url) == len(prefix):
        return False
    if any(part in url for part in _FORBIDDEN_IN_URL):
        return False
    return all(character.isprintable() and not character.isspace() for character in url)


def sniff_image_type(head: bytes) -> str | None:
    """The image type the bytes really are, or None when they are no allowed image."""
    for magic, mime in _MAGIC:
        if head.startswith(magic):
            return mime
    if head[:4] == _WEBP[0] and head[8:12] == _WEBP[1]:
        return "image/webp"
    return None
