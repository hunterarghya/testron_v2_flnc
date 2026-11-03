"""An assignment's own settings: publication, integrity, password (domain_model.md §3.5)."""

import hashlib
import json
from dataclasses import dataclass

from core.errors import FieldError, FieldsInvalid, Invalid
from core.text import clean_text_line
from modules.assignments.domain.values import PublicationMode, PublishContent

MAX_TITLE_LENGTH = 200
PASSWORD_LENGTH = (4, 32)
MAX_DELAY_S = 30 * 24 * 3600
# The same ranges as a test's own integrity settings (domain_model.md §4.2)
GRACE_SECONDS = (0, 60)
MAX_WARNINGS = (1, 20)


class PasswordMismatch(Invalid):
    """The two password boxes differ (D-07)."""

    code = "password_mismatch"
    title = "The two passwords don't match"


@dataclass(frozen=True, slots=True)
class Publication:
    mode: PublicationMode = PublicationMode.MANUAL
    delay_s: int | None = None
    content: PublishContent = PublishContent.SCORE_ONLY
    show_paper: bool = False
    show_solutions: bool = False
    show_rank_and_stats: bool = False


@dataclass(frozen=True, slots=True)
class Integrity:
    grace_s: int
    max_warnings: int
    action: str


def ensure_publication_valid(publication: Publication) -> None:
    delayed = publication.mode is PublicationMode.AUTO_DELAYED
    delay = publication.delay_s
    if delayed and (delay is None or not 0 < delay <= MAX_DELAY_S):
        raise FieldsInvalid(
            FieldError("publication.delay_s", "invalid", "Use a delay of up to 30 days")
        )
    if not delayed and delay is not None:
        raise FieldsInvalid(
            FieldError("publication.delay_s", "invalid", "Only a delayed publication has a delay")
        )


def ensure_integrity_valid(integrity: Integrity) -> None:
    errors = []
    if not GRACE_SECONDS[0] <= integrity.grace_s <= GRACE_SECONDS[1]:
        errors.append(FieldError("integrity.grace_s", "invalid", "Use 0 to 60"))
    if not MAX_WARNINGS[0] <= integrity.max_warnings <= MAX_WARNINGS[1]:
        errors.append(FieldError("integrity.max_warnings", "invalid", "Use 1 to 20"))
    if errors:
        raise FieldsInvalid(*errors)


def assignment_title(raw: str) -> str:
    title = clean_text_line(raw)
    if not title or len(title) > MAX_TITLE_LENGTH:
        raise FieldsInvalid(
            FieldError("title", "invalid", f"Use 1 to {MAX_TITLE_LENGTH} characters")
        )
    return title


def checked_password(password: str, confirm: str | None) -> str:
    """The teacher types it twice (domain_model.md §3.5 #4); 4 to 32 characters, kept as typed."""
    low, high = PASSWORD_LENGTH
    if not low <= len(password) <= high:
        raise FieldsInvalid(FieldError("password", "invalid", f"Use {low} to {high} characters"))
    if password != confirm:
        raise PasswordMismatch()
    return password


def content_hash(paper: dict[str, object]) -> str:
    """SHA-256 of the paper's canonical JSON (sorted keys, no spaces)."""
    canonical = json.dumps(paper, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()
