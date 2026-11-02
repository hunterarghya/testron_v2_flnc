"""Upload rules, image addresses and the signature (editor_content_spec.md §2.3, §5.1)."""

from datetime import UTC, datetime

import pytest

from core.errors import FieldsInvalid
from modules.media.domain.signing import is_signature_valid, upload_signature
from modules.media.domain.uploads import (
    MAX_UPLOAD_BYTES,
    ensure_upload_allowed,
    is_url_under,
    sniff_image_type,
    upload_folder,
)

PREFIX = "https://ik.imagekit.io/acme/tests/"


@pytest.mark.parametrize("mime", ["image/png", "image/jpeg", "image/webp", "image/gif"])
def test_the_four_image_types_are_allowed(mime: str) -> None:
    ensure_upload_allowed(mime, MAX_UPLOAD_BYTES)


def test_svg_and_big_files_are_refused_together() -> None:
    with pytest.raises(FieldsInvalid) as error:
        ensure_upload_allowed("image/svg+xml", MAX_UPLOAD_BYTES + 1)

    codes = [(e.field, e.code) for e in error.value.field_errors()]
    assert codes == [("mime", "unsupported_type"), ("size_bytes", "too_large")]


def test_uploads_go_into_a_folder_per_month() -> None:
    assert upload_folder("/tests", datetime(2026, 1, 5, tzinfo=UTC)) == "/tests/2026/01"


@pytest.mark.parametrize(
    ("url", "allowed"),
    [
        (f"{PREFIX}2026/11/cell.png", True),
        (PREFIX, False),  # the folder itself, no file
        ("https://ik.imagekit.io/acme/other/cell.png", False),
        ("https://evil.example/tests/cell.png", False),
        ("http://ik.imagekit.io/acme/tests/cell.png", False),
        (f"{PREFIX}cell.png?tr=w-400", False),  # sizes are added when shown, never stored
        (f"{PREFIX}cell.png#x", False),
        (f"{PREFIX}../secrets/cell.png", False),
        (f"{PREFIX}a\\b.png", False),
        (f"{PREFIX}a b.png", False),
        (f"{PREFIX}a\nb.png", False),
        (f"{PREFIX}{'a' * 2048}.png", False),
    ],
)
def test_only_plain_files_inside_the_folder_are_allowed(url: str, allowed: bool) -> None:
    assert is_url_under(url, PREFIX) is allowed


@pytest.mark.parametrize(
    ("head", "mime"),
    [
        (b"\x89PNG\r\n\x1a\n....", "image/png"),
        (b"\xff\xd8\xff\xe0....", "image/jpeg"),
        (b"GIF89a....", "image/gif"),
        (b"GIF87a....", "image/gif"),
        (b"RIFF\x10\x00\x00\x00WEBPVP8 ", "image/webp"),
        (b"RIFF\x10\x00\x00\x00WAVEfmt ", None),
        (b"<svg xmlns='http://www.w3.org/2000/svg'>", None),
        (b"", None),
    ],
)
def test_the_real_type_comes_from_the_first_bytes(head: bytes, mime: str | None) -> None:
    assert sniff_image_type(head) == mime


def test_signature_is_hmac_sha1_hex_of_token_and_expiry() -> None:
    signature = upload_signature("private", token="t-1", expire=1_800_000_000)

    assert len(signature) == 40
    assert is_signature_valid("private", token="t-1", expire=1_800_000_000, signature=signature)
    assert not is_signature_valid("other", token="t-1", expire=1_800_000_000, signature=signature)
    assert not is_signature_valid("private", token="t-1", expire=1_800_000_001, signature=signature)
