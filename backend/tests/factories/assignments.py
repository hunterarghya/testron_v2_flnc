"""A test that can be assigned, and the wizard's answers for it (not the use cases' rules)."""

from collections.abc import Sequence
from dataclasses import fields, replace
from typing import Any
from uuid import UUID

from modules.assignments.domain.assignment import Settings
from modules.assignments.domain.settings import Integrity, Publication
from modules.assignments.domain.values import WindowKind
from modules.assignments.domain.window import Window
from modules.assignments.services.commands.create_assignment import NewAssignment
from modules.authoring.models import Test
from tests.factories.authoring import make_question, make_section, make_test

SETTINGS = Settings(
    title="Cell Biology",
    window=Window(WindowKind.OPEN),
    requires_activation=False,
    integrity=Integrity(grace_s=5, max_warnings=3, action="AUTO_SUBMIT"),
    publication=Publication(),
)
_SETTING_NAMES = {field.name for field in fields(Settings)}


def assignable_test(**test_fields: object) -> Test:
    """A one-question test with no problems."""
    test = make_test(**test_fields)
    make_question(make_section(test))
    return test


def new_assignment(test_id: UUID, student_ids: Sequence[UUID], **changes: Any) -> NewAssignment:
    """`changes` may set Settings fields (title, window, …) or NewAssignment ones (password, …)."""
    settings = replace(SETTINGS, **{k: v for k, v in changes.items() if k in _SETTING_NAMES})
    rest = {k: v for k, v in changes.items() if k not in _SETTING_NAMES}
    return NewAssignment(test_id=test_id, settings=settings, student_ids=student_ids, **rest)
