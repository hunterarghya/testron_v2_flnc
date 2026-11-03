"""An assignment as the use cases see it: what the teacher chose, and what is stored."""

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from modules.assignments.domain.lifecycle import Timeline
from modules.assignments.domain.settings import (
    Integrity,
    Publication,
    assignment_title,
    ensure_integrity_valid,
    ensure_publication_valid,
)
from modules.assignments.domain.window import Window


@dataclass(frozen=True, slots=True)
class Settings:
    """Everything the wizard sets, apart from the test, audience, password and timing."""

    title: str
    window: Window
    requires_activation: bool
    integrity: Integrity
    publication: Publication


@dataclass(frozen=True, slots=True)
class AssignmentRecord:
    id: UUID
    test_id: UUID
    settings: Settings
    timeline: Timeline
    has_password: bool
    timing_kind: str
    published_at: datetime | None


@dataclass(frozen=True, slots=True)
class Progress:
    """How far the audience has got: attempts ended and still going."""

    ended: int = 0
    in_progress: int = 0


@dataclass(frozen=True, slots=True)
class SettingsPatch:
    """An edit from the overview (T-08): None leaves that setting as it is."""

    title: str | None = None
    window: Window | None = None
    requires_activation: bool | None = None
    integrity: Integrity | None = None
    publication: Publication | None = None

    def changed_fields(self) -> list[str]:
        """The editable-field names (domain/editing.py) this patch touches."""
        named = {
            "title": self.title,
            "window": self.window,
            "gate": self.requires_activation,
            "integrity": self.integrity,
            "publication": self.publication,
        }
        return [name for name, value in named.items() if value is not None]

    def applied_to(self, settings: Settings) -> Settings:
        return Settings(
            title=_or(self.title, settings.title),
            window=_or(self.window, settings.window),
            requires_activation=_or(self.requires_activation, settings.requires_activation),
            integrity=_or(self.integrity, settings.integrity),
            publication=_or(self.publication, settings.publication),
        )


def checked_settings(settings: Settings) -> Settings:
    """The settings with a clean title, once publication and integrity are valid. The window
    is checked on its own: only when it is set or changed (it may be in the past by now)."""
    ensure_publication_valid(settings.publication)
    ensure_integrity_valid(settings.integrity)
    return replace(settings, title=assignment_title(settings.title))


def _or[T](new: T | None, old: T) -> T:
    return old if new is None else new
