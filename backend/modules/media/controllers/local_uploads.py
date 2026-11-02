"""The local dev adapter's upload endpoint: a stand-in for ImageKit's, same form fields and
same answer, so the browser code doesn't know the difference (ADR-060)."""

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.clock import get_clock
from modules.media.domain.errors import UploadRejected
from modules.media.domain.uploads import MAX_UPLOAD_BYTES
from modules.media.services.commands.store_local_upload import SignedUpload, store_local_upload


# Like ImageKit's, this form is authorized by its upload signature, not by a session cookie
@csrf_exempt
@require_POST
def receive_upload(request: HttpRequest) -> JsonResponse:
    upload = request.FILES.get("file")
    try:
        signed = SignedUpload(
            token=request.POST.get("token", ""),
            expire=int(request.POST.get("expire", "0")),
            signature=request.POST.get("signature", ""),
            folder=request.POST.get("folder", ""),
        )
        if upload is None:
            raise UploadRejected()
        # One byte past the limit is enough to know it's too big
        data = upload.read(MAX_UPLOAD_BYTES + 1)
        stored = store_local_upload(signed, data=data, now=get_clock().now())
    except (ValueError, UploadRejected):
        return JsonResponse({"message": UploadRejected.title}, status=400)
    return JsonResponse(
        {
            "fileId": stored.file_id,
            "name": stored.name,
            "url": stored.url,
            "filePath": stored.file_path,
            "size": stored.size,
            "fileType": "image",
        }
    )
