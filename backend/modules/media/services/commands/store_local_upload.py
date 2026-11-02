import re
from dataclasses import dataclass
from datetime import datetime

from core.ids import uuid7
from modules.media.domain.errors import UploadRejected
from modules.media.domain.signing import is_signature_valid
from modules.media.domain.uploads import (
    IMAGE_TYPES,
    MAX_UPLOAD_BYTES,
    SIGNATURE_LIFETIME,
    sniff_image_type,
)
from modules.media.repositories.local_files import save_local_file
from modules.media.services.storage_target import TESTS_FOLDER, current_target

# What sign_image_upload hands out: /tests/YYYY/MM
_FOLDER = re.compile(rf"^{TESTS_FOLDER}/\d{{4}}/\d{{2}}$")


@dataclass(frozen=True, slots=True)
class SignedUpload:
    token: str
    expire: int
    signature: str
    folder: str


@dataclass(frozen=True, slots=True)
class StoredFile:
    """Shaped like ImageKit's upload response, so the browser handles both the same way."""

    file_id: str
    name: str
    url: str
    file_path: str
    size: int


def store_local_upload(signed: SignedUpload, *, data: bytes, now: datetime) -> StoredFile:
    """The local dev adapter's upload endpoint (dev_environment_and_deployment.md §1.6).

    It checks what ImageKit checks (the signature, its expiry, the file's real type and
    size), then keeps the file under a fresh name, so names never collide.
    """
    target = current_target()
    if not target.is_local:
        raise UploadRejected()
    _ensure_signed(signed, now=now)
    mime = sniff_image_type(data[:16])
    if mime is None or len(data) > MAX_UPLOAD_BYTES:
        raise UploadRejected(context={"reason": "type_or_size"})
    file_id = uuid7().hex
    name = f"{file_id}.{IMAGE_TYPES[mime]}"
    file_path = f"{signed.folder}/{name}"
    save_local_file(file_path.lstrip("/"), data)
    return StoredFile(
        file_id=file_id,
        name=name,
        url=f"{target.url_endpoint}{file_path}",
        file_path=file_path,
        size=len(data),
    )


def _ensure_signed(signed: SignedUpload, *, now: datetime) -> None:
    unix_now = int(now.timestamp())
    fresh = unix_now < signed.expire <= unix_now + int(SIGNATURE_LIFETIME.total_seconds())
    valid = is_signature_valid(
        current_target().private_key,
        token=signed.token,
        expire=signed.expire,
        signature=signed.signature,
    )
    if not (fresh and valid and _FOLDER.match(signed.folder)):
        raise UploadRejected(context={"reason": "signature"})
