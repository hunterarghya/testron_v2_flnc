"""The local dev adapter checks uploads as ImageKit would (dev_environment_and_deployment §1.6)."""

from collections.abc import Callable
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from conftest import TEST_NOW, MakeCtx
from core.context import Actor, Role
from modules.media.domain.errors import UploadRejected
from modules.media.public import is_allowed_image_url
from modules.media.services.commands.sign_image_upload import sign_image_upload
from modules.media.services.commands.store_local_upload import SignedUpload, store_local_upload
from modules.media.tests.conftest import UseImageKit

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture
def signed(make_ctx: MakeCtx) -> SignedUpload:
    ctx = make_ctx(Actor(user_id=uuid4(), role=Role.TEACHER))
    ticket = sign_image_upload(ctx, mime="image/png", size_bytes=len(PNG_BYTES))
    return SignedUpload(
        token=ticket.token, expire=ticket.expire, signature=ticket.signature, folder=ticket.folder
    )


def test_a_signed_image_is_stored_and_may_be_used_in_content(
    signed: SignedUpload, media_root: Path
) -> None:
    stored = store_local_upload(signed, data=PNG_BYTES, now=TEST_NOW)

    assert stored.name.endswith(".png")
    assert stored.url == f"/dev-media/tests/2026/11/{stored.name}"
    assert (media_root / "tests" / "2026" / "11" / stored.name).read_bytes() == PNG_BYTES
    assert is_allowed_image_url(stored.url)


def test_names_never_collide(signed: SignedUpload) -> None:
    first = store_local_upload(signed, data=PNG_BYTES, now=TEST_NOW)
    second = store_local_upload(signed, data=PNG_BYTES, now=TEST_NOW)

    assert first.name != second.name


@pytest.mark.parametrize(
    "tamper",
    [
        lambda s: replace(s, signature="0" * 40),
        lambda s: replace(s, token="someone-elses-token"),
        lambda s: replace(s, expire=s.expire + 60),
        lambda s: replace(s, folder="/tests/../../config"),
        lambda s: replace(s, folder="/elsewhere/2026/11"),
    ],
)
def test_a_tampered_upload_is_refused(
    signed: SignedUpload, tamper: Callable[[SignedUpload], SignedUpload]
) -> None:
    with pytest.raises(UploadRejected):
        store_local_upload(tamper(signed), data=PNG_BYTES, now=TEST_NOW)


def test_an_expired_signature_is_refused(signed: SignedUpload) -> None:
    later = TEST_NOW + timedelta(minutes=10)

    with pytest.raises(UploadRejected):
        store_local_upload(signed, data=PNG_BYTES, now=later)


@pytest.mark.parametrize(
    "data",
    [
        b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>",
        PNG_BYTES + b"\x00" * (5 * 1024 * 1024),
    ],
)
def test_files_that_are_no_allowed_image_are_refused(signed: SignedUpload, data: bytes) -> None:
    with pytest.raises(UploadRejected):
        store_local_upload(signed, data=data, now=TEST_NOW)


def test_nothing_is_stored_with_the_imagekit_backend(
    signed: SignedUpload, use_imagekit: UseImageKit
) -> None:
    use_imagekit()

    with pytest.raises(UploadRejected):
        store_local_upload(signed, data=PNG_BYTES, now=TEST_NOW)
