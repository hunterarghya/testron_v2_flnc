"""record() and the append-only audit table (database_schema.md §3.8, security.md T-07)."""

from uuid import uuid4

import pytest
from django.db import IntegrityError, transaction

from conftest import MakeCtx
from core.context import Actor, Role
from modules.audit.models import AuditEntry
from modules.audit.public import entries_for, record
from tests.factories.identity import make_user

pytestmark = pytest.mark.django_db


def test_record_notes_who_did_what_to_what(make_ctx: MakeCtx) -> None:
    teacher = make_user(teacher=True)
    target = uuid4()

    record(
        make_ctx(Actor(user_id=teacher.id, role=Role.TEACHER)),
        action="assignment.reveal_password",
        target_type="assignment",
        target_id=target,
    )
    record(
        make_ctx(),
        action="attempt.finalize",
        target_type="assignment",
        target_id=target,
        data={"n": 1},
    )

    assert entries_for("assignment", target) == [
        ("attempt.finalize", None, {"n": 1}),
        ("assignment.reveal_password", teacher.id, {}),
    ]


def test_entries_cannot_be_changed_or_deleted(make_ctx: MakeCtx) -> None:
    record(make_ctx(), action="x.y", target_type="t", target_id=uuid4())

    with pytest.raises(IntegrityError), transaction.atomic():
        AuditEntry.objects.update(action="rewritten")
    with pytest.raises(IntegrityError), transaction.atomic():
        AuditEntry.objects.all().delete()


def test_a_deleted_user_is_forgotten_but_the_entry_stays(make_ctx: MakeCtx) -> None:
    user = make_user()
    record(
        make_ctx(Actor(user_id=user.id, role=Role.STUDENT)),
        action="x.y",
        target_type="t",
        target_id=uuid4(),
    )

    AuditEntry.objects.update(actor=None)

    assert AuditEntry.objects.get().actor_id is None
