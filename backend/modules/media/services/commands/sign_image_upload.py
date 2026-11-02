from dataclasses import dataclass
from uuid import uuid4

from core.context import Ctx
from modules.media.domain.signing import upload_signature
from modules.media.domain.uploads import SIGNATURE_LIFETIME, ensure_upload_allowed, upload_folder
from modules.media.policies import ensure_teacher_can_upload
from modules.media.services.storage_target import current_target


@dataclass(frozen=True, slots=True)
class UploadTicket:
    token: str
    # Unix seconds after which the signature stops working
    expire: int
    signature: str
    public_key: str
    url_endpoint: str
    folder: str
    upload_url: str


def sign_image_upload(ctx: Ctx, *, mime: str, size_bytes: int) -> UploadTicket:
    """Let the browser upload one image straight to storage (domain_model.md §8, ADR-009).

    The type and size are checked first. The signature lasts 10 minutes, and its token is
    fresh each time (ImageKit refuses a token it has seen before).
    """
    ensure_teacher_can_upload(ctx.actor)
    ensure_upload_allowed(mime, size_bytes)
    target = current_target()
    token = str(uuid4())
    expire = int((ctx.now + SIGNATURE_LIFETIME).timestamp())
    return UploadTicket(
        token=token,
        expire=expire,
        signature=upload_signature(target.private_key, token=token, expire=expire),
        public_key=target.public_key,
        url_endpoint=target.url_endpoint,
        folder=upload_folder(target.root_folder, ctx.now),
        upload_url=target.upload_url,
    )
