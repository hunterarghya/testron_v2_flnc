"""HTTP contract of the upload signature (api_contract.md §2.4) and the local dev adapter."""

import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory

from core.clock import FrozenClock
from modules.media.controllers.local_uploads import receive_upload
from tests.clients import logged_in, send
from tests.factories.identity import make_user

pytestmark = pytest.mark.django_db
SIGN = "/api/v1/admin/media/upload-signature"
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture
def teacher(frozen_clock: FrozenClock) -> Client:
    return logged_in(make_user(teacher=True).email)


def sign(client: Client, **body: object) -> dict[str, object]:
    request = {"file_name": "cell.png", "mime": "image/png", "size_bytes": 68} | body
    response = send(client, "post", SIGN, request)
    assert response.status_code == 200
    signed: dict[str, object] = response.json()
    return signed


def upload(form: dict[str, object]) -> dict[str, object]:
    request = RequestFactory().post("/dev-media/upload", form)
    response = receive_upload(request)
    return {"status": response.status_code, **json.loads(response.content)}


def test_signature_has_everything_the_browser_needs(teacher: Client) -> None:
    signed = sign(teacher)

    assert set(signed) == {
        "token",
        "expire",
        "signature",
        "public_key",
        "url_endpoint",
        "folder",
        "upload_url",
    }


def test_wrong_type_is_a_field_error(teacher: Client) -> None:
    response = send(
        teacher, "post", SIGN, {"file_name": "x.svg", "mime": "image/svg+xml", "size_bytes": 10}
    )

    assert response.status_code == 422
    assert [error["field"] for error in response.json()["errors"]] == ["mime"]


def test_signed_upload_to_the_local_adapter_answers_like_imagekit(teacher: Client) -> None:
    signed = sign(teacher)
    form = {key: signed[key] for key in ("token", "expire", "signature", "folder")}

    stored = upload(form | {"file": SimpleUploadedFile("cell.png", PNG_BYTES)})

    assert stored["status"] == 200
    assert str(stored["url"]).startswith("/dev-media/tests/2026/11/")
    assert set(stored) >= {"fileId", "name", "url", "filePath", "size", "fileType"}


def test_unsigned_upload_is_400(teacher: Client) -> None:
    stored = upload({"expire": "x", "file": SimpleUploadedFile("cell.png", PNG_BYTES)})

    assert stored == {"status": 400, "message": "The upload was refused"}


def test_upload_without_a_file_is_400(teacher: Client) -> None:
    signed = sign(teacher)
    form = {key: signed[key] for key in ("token", "expire", "signature", "folder")}

    assert upload(form)["status"] == 400
