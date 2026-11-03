"""Assignment rows <-> the domain's values: the one place that knows the column names."""

from modules.assignments.domain.assignment import AssignmentRecord, Settings
from modules.assignments.domain.lifecycle import Timeline
from modules.assignments.domain.settings import Integrity, Publication
from modules.assignments.domain.values import PublicationMode, PublishContent, WindowKind
from modules.assignments.domain.window import Window
from modules.assignments.models import Assignment


def settings_columns(settings: Settings) -> dict[str, object]:
    window, integrity, publication = settings.window, settings.integrity, settings.publication
    return {
        "title": settings.title,
        "window_kind": window.kind.value,
        "planned_at": window.planned_at,
        "starts_at": window.starts_at,
        "opens_at": window.opens_at,
        "closes_at": window.closes_at,
        "late_entry_s": window.late_entry_s,
        "requires_activation": settings.requires_activation,
        "integrity_grace_s": integrity.grace_s,
        "integrity_max_warnings": integrity.max_warnings,
        "integrity_action": integrity.action,
        **publication_columns(publication),
    }


def publication_columns(publication: Publication) -> dict[str, object]:
    return {
        "publication_mode": publication.mode.value,
        "publication_delay_s": publication.delay_s,
        "publish_content": publication.content.value,
        "show_paper": publication.show_paper,
        "show_solutions": publication.show_solutions,
        "show_rank_and_stats": publication.show_rank_and_stats,
    }


def record_of(row: Assignment) -> AssignmentRecord:
    settings = settings_of(row)
    return AssignmentRecord(
        id=row.id,
        test_id=row.test_id,
        settings=settings,
        timeline=Timeline(
            window=settings.window,
            requires_activation=row.requires_activation,
            total_duration_s=row.total_duration_s,
            activated_at=row.activated_at,
            ended_at=row.ended_at,
            cancelled_at=row.cancelled_at,
        ),
        has_password=row.password_ciphertext is not None,
        timing_kind=row.timing_kind,
        published_at=row.published_at,
        source_group_ids=tuple(row.source_group_ids),
    )


def settings_of(row: Assignment) -> Settings:
    return Settings(
        title=row.title,
        window=Window(
            kind=WindowKind(row.window_kind),
            planned_at=row.planned_at,
            starts_at=row.starts_at,
            opens_at=row.opens_at,
            closes_at=row.closes_at,
            late_entry_s=row.late_entry_s,
        ),
        requires_activation=row.requires_activation,
        integrity=Integrity(
            row.integrity_grace_s, row.integrity_max_warnings, row.integrity_action
        ),
        publication=Publication(
            mode=PublicationMode(row.publication_mode),
            delay_s=row.publication_delay_s,
            content=PublishContent(row.publish_content),
            show_paper=row.show_paper,
            show_solutions=row.show_solutions,
            show_rank_and_stats=row.show_rank_and_stats,
        ),
    )
