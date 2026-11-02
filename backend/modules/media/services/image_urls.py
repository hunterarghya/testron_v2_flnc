from modules.media.domain.uploads import is_url_under
from modules.media.services.storage_target import current_target


def is_allowed_image_url(url: str) -> bool:
    """True when content may show this image: one of ours, in the upload folder (security.md
    §4, `test_image_src_outside_imagekit_rejected`). Locally that's `/dev-media/tests/…`."""
    return is_url_under(url, current_target().allowed_prefix)
