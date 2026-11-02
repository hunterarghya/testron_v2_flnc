"""Every media endpoint: path + method -> controller (ADR-030). No logic here."""

from django.conf import settings
from django.urls import URLPattern, path, re_path
from django.views.static import serve
from ninja import Router

from core.http.areas import TeacherArea
from modules.media.controllers import uploads
from modules.media.controllers.local_uploads import receive_upload
from modules.media.dto.uploads import UploadSignatureOut

router = Router(tags=["media"], auth=TeacherArea())

router.add_api_operation(
    "/admin/media/upload-signature",
    ["POST"],
    uploads.sign_image_upload,
    response={200: UploadSignatureOut},
    summary="Sign one image upload straight from the browser to storage",
)


def local_dev_urlpatterns() -> list[URLPattern]:
    """The local dev adapter's upload and file URLs (outside the API, like ImageKit's own).
    Mounted only when DEBUG is on and MEDIA_BACKEND=local."""
    return [
        path("dev-media/upload", receive_upload),
        re_path(r"^dev-media/(?P<path>.+)$", serve, {"document_root": settings.LOCAL_MEDIA_ROOT}),
    ]
