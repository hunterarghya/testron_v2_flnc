"""Publishing results (domain_model.md §6.4; D-01, T-11). Publishing makes every result
visible now, whatever automatic mode was set; unpublishing hides them all again ("Awaiting
results", E-28). Changing the mode starts that mode afresh."""

from dataclasses import dataclass, replace
from datetime import datetime

from modules.assignments.domain.settings import Publication, ensure_publication_valid
from modules.assignments.domain.values import PublicationMode, PublishContent


@dataclass(frozen=True, slots=True)
class PublicationChanges:
    """None leaves that part as it is."""

    mode: PublicationMode | None = None
    delay_s: int | None = None
    content: PublishContent | None = None
    show_paper: bool | None = None
    show_solutions: bool | None = None
    show_rank_and_stats: bool | None = None


@dataclass(frozen=True, slots=True)
class Published:
    publication: Publication
    published_at: datetime | None


def changed(current: Publication, changes: PublicationChanges) -> Publication:
    mode = changes.mode or current.mode
    updated = replace(
        current,
        mode=mode,
        delay_s=_delay(mode, changes.delay_s, current.delay_s),
        content=changes.content or current.content,
        show_paper=_or(changes.show_paper, current.show_paper),
        show_solutions=_or(changes.show_solutions, current.show_solutions),
        show_rank_and_stats=_or(changes.show_rank_and_stats, current.show_rank_and_stats),
    )
    ensure_publication_valid(updated)
    return updated


def publish(current: Publication, changes: PublicationChanges, *, now: datetime) -> Published:
    """Visible now: manual mode, published at this instant, with any option changes."""
    options = changed(current, replace(changes, mode=PublicationMode.MANUAL, delay_s=None))
    return Published(options, now)


def unpublish(current: Publication) -> Published:
    return Published(replace(current, mode=PublicationMode.MANUAL, delay_s=None), None)


def edit(
    current: Publication, published_at: datetime | None, changes: PublicationChanges
) -> Published:
    """A new mode starts afresh (not published); other changes keep the publish time."""
    updated = changed(current, changes)
    return Published(updated, None if updated.mode is not current.mode else published_at)


def _delay(mode: PublicationMode, new: int | None, old: int | None) -> int | None:
    """A delay belongs to AUTO_DELAYED only: switching away drops it."""
    if mode is not PublicationMode.AUTO_DELAYED:
        return None
    return old if new is None else new


def _or(new: bool | None, old: bool) -> bool:
    return old if new is None else new
