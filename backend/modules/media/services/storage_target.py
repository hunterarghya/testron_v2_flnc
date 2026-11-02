"""Where images are uploaded to and served from: ImageKit, or the local dev stand-in.

Both speak ImageKit's upload protocol (architecture.md §5.9), so they differ only in these
values. `MEDIA_BACKEND=local` stores files under `backend/.media/`, served at `/dev-media/`
while DEBUG is on (dev_environment_and_deployment.md §1.6).
"""

import hashlib
import hmac
from dataclasses import dataclass

from django.conf import settings

from core.config import Settings, get_settings

IMAGEKIT_UPLOAD_URL = "https://upload.imagekit.io/api/v1/files/upload"
LOCAL_URL_ENDPOINT = "/dev-media"
LOCAL_UPLOAD_URL = f"{LOCAL_URL_ENDPOINT}/upload"
LOCAL_PUBLIC_KEY = "local"
TESTS_FOLDER = "/tests"
# A real ImageKit account used from a developer's machine keeps its files apart
DEV_TESTS_FOLDER = "/dev/tests"


@dataclass(frozen=True, slots=True)
class StorageTarget:
    public_key: str
    private_key: str
    url_endpoint: str
    upload_url: str
    root_folder: str
    # The local dev adapter: uploads arrive at our own /dev-media/upload
    is_local: bool = False

    @property
    def allowed_prefix(self) -> str:
        """Every image in content must start with this (editor_content_spec.md §2.3)."""
        return f"{self.url_endpoint}{self.root_folder}/"


def current_target() -> StorageTarget:
    config = get_settings()
    return _imagekit(config) if config.media_backend == "imagekit" else _local()


def _imagekit(config: Settings) -> StorageTarget:
    if not (
        config.imagekit_public_key and config.imagekit_private_key and config.imagekit_url_endpoint
    ):
        # core.config already refuses to start without them; this keeps mypy honest
        raise RuntimeError("IMAGEKIT_* is not configured")
    return StorageTarget(
        public_key=config.imagekit_public_key,
        private_key=config.imagekit_private_key.get_secret_value(),
        url_endpoint=config.imagekit_url_endpoint.rstrip("/"),
        upload_url=IMAGEKIT_UPLOAD_URL,
        root_folder=TESTS_FOLDER if config.django_env == "prod" else DEV_TESTS_FOLDER,
    )


def _local() -> StorageTarget:
    return StorageTarget(
        public_key=LOCAL_PUBLIC_KEY,
        private_key=_local_signing_key(),
        url_endpoint=LOCAL_URL_ENDPOINT,
        upload_url=LOCAL_UPLOAD_URL,
        root_folder=TESTS_FOLDER,
        is_local=True,
    )


def _local_signing_key() -> str:
    # Derived, so the app's SECRET_KEY itself never signs anything a browser sees
    secret: str = settings.SECRET_KEY
    return hmac.new(secret.encode(), b"local-media-uploads", hashlib.sha256).hexdigest()
