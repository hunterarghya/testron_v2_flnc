"""Email addresses: one canonical form, and a masked form safe to show (domain_model.md §3.1)."""

from core.errors import Invalid

MAX_EMAIL_LENGTH = 254
_MASK = "•••"
# The part after @ needs at least a name and a top-level domain ("gmail.com")
_MIN_DOMAIN_LABELS = 2


class InvalidEmail(Invalid, ValueError):
    """Also a ValueError, so request validation reports it against the email field."""

    code = "validation_error"
    title = "Enter a valid email address"


def normalize_email(raw: str) -> str:
    """Trimmed and lower-cased, so one address is one account however it was typed."""
    email = raw.strip().lower()
    local, at, domain = email.partition("@")
    if not (local and at and _is_domain(domain)) or len(email) > MAX_EMAIL_LENGTH:
        raise InvalidEmail()
    if any(character.isspace() for character in email) or "@" in domain:
        raise InvalidEmail()
    return email


def mask_email(email: str) -> str:
    """`rina@gmail.com` → `r•••@gmail.com`: enough to recognise, not enough to harvest."""
    local, _, domain = email.partition("@")
    return f"{local[:1]}{_MASK}@{domain}"


def _is_domain(domain: str) -> bool:
    labels = domain.split(".")
    return len(labels) >= _MIN_DOMAIN_LABELS and all(labels)
