from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import SecretStr
from pytest_django.fixtures import Settings as DjangoSettings

from core.config import Settings, get_settings
from modules.media.services import storage_target

UseImageKit = Callable[..., None]


@pytest.fixture(autouse=True)
def media_root(settings: DjangoSettings, tmp_path: Path) -> Path:
    """Local uploads land in a throwaway folder, never in backend/.media/."""
    settings.LOCAL_MEDIA_ROOT = tmp_path
    return tmp_path


@pytest.fixture
def use_imagekit(monkeypatch: pytest.MonkeyPatch) -> UseImageKit:
    """Switch to the ImageKit backend with fake keys (tests run with MEDIA_BACKEND=local)."""

    def switch(**values: object) -> None:
        configured: Settings = get_settings().model_copy(
            update={
                "media_backend": "imagekit",
                "imagekit_public_key": "public_fake",
                "imagekit_private_key": SecretStr("private_fake"),
                "imagekit_url_endpoint": "https://ik.imagekit.io/acme/",
                **values,
            }
        )
        monkeypatch.setattr(storage_target, "get_settings", lambda: configured)

    return switch
