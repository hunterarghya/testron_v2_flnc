from django.http import HttpRequest

from core.http.context import ctx_from
from modules.media.dto.uploads import UploadSignatureIn, UploadSignatureOut
from modules.media.services.commands import sign_image_upload as signing


def sign_image_upload(request: HttpRequest, payload: UploadSignatureIn) -> UploadSignatureOut:
    ticket = signing.sign_image_upload(
        ctx_from(request), mime=payload.mime, size_bytes=payload.size_bytes
    )
    return UploadSignatureOut.from_ticket(ticket)
