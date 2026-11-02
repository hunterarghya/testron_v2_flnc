"""Two merges at once, in opposite directions: no deadlock, no lost question, no crash
(build_phases.md Phase 2 required tests, database_schema.md §5.1)."""

from uuid import uuid4

import pytest

from conftest import MakeCtx
from core.context import Actor, Role
from modules.authoring.services.commands.rename_tag import rename_tag
from modules.authoring.services.queries.list_tags_with_usage import list_tags_with_usage
from modules.tagging.public import TagKind, ensure_tags_by_name
from tests.concurrency import run_together
from tests.factories.authoring import make_question, make_section, make_test

pytestmark = pytest.mark.django_db(transaction=True)


def test_opposite_merges_leave_one_tag_with_every_question(make_ctx: MakeCtx) -> None:
    ctx = make_ctx(Actor(user_id=uuid4(), role=Role.TEACHER))
    typo, real = ensure_tags_by_name(ctx, kind=TagKind.CHAPTER, names=["Genetcs", "Genetics"])
    section = make_section(make_test())
    make_question(section, 0, tag_ids=[typo.id])
    make_question(section, 1, tag_ids=[real.id])

    outcomes = run_together(
        lambda: rename_tag(ctx, tag_id=typo.id, name="Genetics", merge=True),
        lambda: rename_tag(ctx, tag_id=real.id, name="Genetcs", merge=True),
    )

    left = list_tags_with_usage(ctx, kind=TagKind.CHAPTER, search=None)
    assert [type(outcome).__name__ for outcome in outcomes].count("RenameTagResult") >= 1
    assert all(type(outcome).__name__ in ("RenameTagResult", "NotFound") for outcome in outcomes)
    assert len(left) == 1
    assert left[0].question_count == 2
