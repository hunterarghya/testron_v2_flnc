"""Files of the local dev adapter, kept on disk under `LOCAL_MEDIA_ROOT` (`backend/.media/`)."""

from pathlib import Path

from django.conf import settings


def local_media_root() -> Path:
    root: Path = settings.LOCAL_MEDIA_ROOT
    return root


def save_local_file(relative_path: str, data: bytes) -> None:
    path = local_media_root() / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
