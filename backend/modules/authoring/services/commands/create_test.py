from django.db import transaction

from core.context import Ctx
from modules.authoring.domain.app_settings import DEFAULT_APP_SETTINGS
from modules.authoring.domain.document import TestDocumentView
from modules.authoring.domain.drafts import Integrity, Marking, TestSettings, Timing
from modules.authoring.domain.structure import DEFAULT_DURATION_S
from modules.authoring.domain.values import TimingKind
from modules.authoring.policies import ensure_teacher
from modules.authoring.repositories import app_settings, sections, tests_table
from modules.authoring.services.editing import read_document

UNTITLED = "Untitled test"


def create_test(ctx: Ctx) -> TestDocumentView:
    """A new, untitled draft with the teacher's defaults and one (hidden) section
    (T-02 "New test", domain_model.md §3.4 invariant 1)."""
    ensure_teacher(ctx.actor)
    defaults = app_settings.find_app_settings() or DEFAULT_APP_SETTINGS
    settings = TestSettings(
        timing=Timing(TimingKind.TOTAL, duration_s=DEFAULT_DURATION_S),
        shuffle_questions=False,
        shuffle_options=False,
        marking=Marking(defaults.default_marks, defaults.default_negative_marks),
        integrity=Integrity(
            grace_s=defaults.default_integrity_grace_s,
            max_warnings=defaults.default_integrity_max_warnings,
            action=defaults.default_integrity_action,
        ),
    )
    with transaction.atomic():
        test_id = tests_table.insert_test(title=UNTITLED, settings=settings, now=ctx.now)
        sections.insert_section(test_id, position=0, title="", duration_s=None)
    return read_document(test_id)
