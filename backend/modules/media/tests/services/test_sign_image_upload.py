"""sign_image_upload and is_allowed_image_url (architecture.md §5.9, security.md §4)."""

from uuid import uuid4

import pytest

from conftest import TEST_NOW, MakeCtx
from core.context import Actor, Ctx, Role, StudentStatus
from core.errors import FieldsInvalid, Forbidden
from modules.media.domain.signing import is_signature_valid
from modules.media.public import is_allowed_image_url
from modules.media.services.commands.sign_image_upload import sign_image_upload
from modules.media.services.storage_target import current_target
from modules.media.tests.conftest import UseImageKit

PNG = "image/png"


@pytest.fixture
def teacher_ctx(make_ctx: MakeCtx) -> Ctx:
    return make_ctx(Actor(user_id=uuid4(), role=Role.TEACHER))


def test_local_signature_points_at_the_dev_adapter(teacher_ctx: Ctx) -> None:
    ticket = sign_image_upload(teacher_ctx, mime=PNG, size_bytes=1000)

    assert (ticket.upload_url, ticket.url_endpoint, ticket.public_key) == (
        "/dev-media/upload",
        "/dev-media",
        "local",
    )
    assert ticket.folder == "/tests/2026/11"
    assert ticket.expire == int(TEST_NOW.timestamp()) + 600
    assert is_signature_valid(
        current_target().private_key,
        token=ticket.token,
        expire=ticket.expire,
        signature=ticket.signature,
    )


def test_every_signature_has_a_fresh_token(teacher_ctx: Ctx) -> None:
    first = sign_image_upload(teacher_ctx, mime=PNG, size_bytes=1000)
    second = sign_image_upload(teacher_ctx, mime=PNG, size_bytes=1000)

    assert first.token != second.token


def test_imagekit_signature_uses_the_account_and_a_dev_folder(
    teacher_ctx: Ctx, use_imagekit: UseImageKit
) -> None:
    use_imagekit()

    ticket = sign_image_upload(teacher_ctx, mime=PNG, size_bytes=1000)

    assert ticket.upload_url == "https://upload.imagekit.io/api/v1/files/upload"
    assert (ticket.public_key, ticket.url_endpoint) == (
        "public_fake",
        "https://ik.imagekit.io/acme",
    )
    assert ticket.folder == "/dev/tests/2026/11"
    assert is_signature_valid(
        "private_fake", token=ticket.token, expire=ticket.expire, signature=ticket.signature
    )


def test_production_uploads_go_to_the_tests_folder(
    teacher_ctx: Ctx, use_imagekit: UseImageKit
) -> None:
    use_imagekit(django_env="prod")

    assert sign_image_upload(teacher_ctx, mime=PNG, size_bytes=1000).folder == "/tests/2026/11"


def test_upload_signature_rejects_svg_and_large(teacher_ctx: Ctx) -> None:
    with pytest.raises(FieldsInvalid):
        sign_image_upload(teacher_ctx, mime="image/svg+xml", size_bytes=1000)
    with pytest.raises(FieldsInvalid):
        sign_image_upload(teacher_ctx, mime=PNG, size_bytes=5 * 1024 * 1024 + 1)


def test_only_the_teacher_gets_a_signature(make_ctx: MakeCtx) -> None:
    student = Actor(user_id=uuid4(), role=Role.STUDENT, student_status=StudentStatus.ACTIVE)

    with pytest.raises(Forbidden):
        sign_image_upload(make_ctx(student), mime=PNG, size_bytes=1000)


def test_image_src_outside_imagekit_rejected(use_imagekit: UseImageKit) -> None:
    use_imagekit()

    assert is_allowed_image_url("https://ik.imagekit.io/acme/dev/tests/2026/11/cell.png")
    assert not is_allowed_image_url("https://ik.imagekit.io/acme/tests/2026/11/cell.png")
    assert not is_allowed_image_url("https://tracker.example/pixel.png")
    assert not is_allowed_image_url("/dev-media/tests/2026/11/cell.png")


def test_local_images_are_allowed_only_with_the_local_adapter() -> None:
    assert is_allowed_image_url("/dev-media/tests/2026/11/cell.png")
    assert not is_allowed_image_url("https://ik.imagekit.io/acme/tests/2026/11/cell.png")
