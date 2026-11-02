"""The only names other modules may import from media (R-08)."""

from modules.media.services.image_urls import is_allowed_image_url

__all__ = ["is_allowed_image_url"]
