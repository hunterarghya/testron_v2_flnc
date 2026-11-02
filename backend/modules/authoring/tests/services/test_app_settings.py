"""get_app_settings, update_app_settings, ensure_app_settings and get_app_info (T-19)."""

from decimal import Decimal
from uuid import uuid4

import pytest

from conftest import TEST_NOW, MakeCtx
from core.clock import FrozenClock
from core.context import Actor, Ctx, Role, StudentStatus
from core.errors import FieldsInvalid, Forbidden
from modules.authoring.domain.app_settings import DEFAULT_APP_SETTINGS
from modules.authoring.domain.values import IntegrityAction
from modules.authoring.public import ensure_app_settings, get_coaching_name
from modules.authoring.services.commands.update_app_settings import update_app_settings
from modules.authoring.services.queries.get_app_info import get_app_info
from modules.authoring.services.queries.get_app_settings import get_app_settings

pytestmark = pytest.mark.django_db
LOGO = "/dev-media/tests/2026/11/logo.png"


@pytest.fixture
def teacher_ctx(make_ctx: MakeCtx) -> Ctx:
    return make_ctx(Actor(user_id=uuid4(), role=Role.TEACHER))


def test_defaults_are_shown_before_anything_is_saved(teacher_ctx: Ctx) -> None:
    assert get_app_settings(teacher_ctx) == DEFAULT_APP_SETTINGS
    assert get_coaching_name() == "Test Platform"


def test_only_the_fields_sent_change(teacher_ctx: Ctx) -> None:
    updated = update_app_settings(
        teacher_ctx, changes={"coaching_name": " Sen's  Biology ", "default_marks": Decimal("2.5")}
    )

    assert (updated.coaching_name, updated.default_marks) == ("Sen's Biology", Decimal("2.50"))
    assert updated.default_negative_marks == Decimal(1)
    assert updated.updated_at == TEST_NOW
    assert get_app_settings(teacher_ctx) == updated


def test_branding_reaches_the_header_and_emails(teacher_ctx: Ctx) -> None:
    update_app_settings(teacher_ctx, changes={"coaching_name": "Sen's Biology", "logo_url": LOGO})

    assert get_app_info().coaching_name == "Sen's Biology"
    assert get_app_info().logo_url == LOGO
    assert get_coaching_name() == "Sen's Biology"


def test_a_logo_from_anywhere_else_is_refused(teacher_ctx: Ctx) -> None:
    with pytest.raises(FieldsInvalid) as error:
        update_app_settings(teacher_ctx, changes={"logo_url": "https://tracker.example/a.png"})

    assert [e.field for e in error.value.field_errors()] == ["logo_url"]


def test_the_logo_can_be_removed(teacher_ctx: Ctx) -> None:
    update_app_settings(teacher_ctx, changes={"logo_url": LOGO})

    assert update_app_settings(teacher_ctx, changes={"logo_url": None}).logo_url is None


def test_bad_values_change_nothing(teacher_ctx: Ctx) -> None:
    with pytest.raises(FieldsInvalid) as error:
        update_app_settings(
            teacher_ctx,
            changes={"coaching_name": "   ", "default_integrity_max_warnings": 21},
        )

    assert [e.field for e in error.value.field_errors()] == [
        "coaching_name",
        "default_integrity_max_warnings",
    ]
    assert get_app_settings(teacher_ctx) == DEFAULT_APP_SETTINGS


def test_integrity_defaults_can_change(teacher_ctx: Ctx) -> None:
    updated = update_app_settings(
        teacher_ctx,
        changes={
            "default_integrity_grace_s": 0,
            "default_integrity_max_warnings": 20,
            "default_integrity_action": IntegrityAction.DISQUALIFY,
        },
    )

    assert (
        updated.default_integrity_grace_s,
        updated.default_integrity_max_warnings,
        updated.default_integrity_action,
    ) == (0, 20, IntegrityAction.DISQUALIFY)


def test_seeding_never_overwrites_the_teachers_choices(
    teacher_ctx: Ctx, make_ctx: MakeCtx, frozen_clock: FrozenClock
) -> None:
    assert ensure_app_settings(make_ctx()) is True
    update_app_settings(teacher_ctx, changes={"coaching_name": "Sen's Biology"})

    assert ensure_app_settings(make_ctx()) is False
    assert get_coaching_name() == "Sen's Biology"


def test_only_the_teacher_sees_and_changes_settings(make_ctx: MakeCtx) -> None:
    student = make_ctx(
        Actor(user_id=uuid4(), role=Role.STUDENT, student_status=StudentStatus.ACTIVE)
    )

    with pytest.raises(Forbidden):
        get_app_settings(student)
    with pytest.raises(Forbidden):
        update_app_settings(student, changes={"coaching_name": "Mine now"})
