import pytest

from conftest import MakeCtx
from modules.tagging.domain.names import TagKind
from modules.tagging.models import Tag
from modules.tagging.services.commands.ensure_tags_by_name import ensure_tags_by_name

pytestmark = pytest.mark.django_db
CHAPTER, TOPIC = TagKind.CHAPTER, TagKind.TOPIC


def test_new_names_become_tags_as_first_typed(make_ctx: MakeCtx) -> None:
    tags = ensure_tags_by_name(make_ctx(), kind=CHAPTER, names=["  Cell  Biology", "কোষ"])

    assert [tag.name for tag in tags] == ["Cell Biology", "কোষ"]
    assert Tag.objects.count() == 2


def test_existing_tags_are_reused_whatever_the_case(make_ctx: MakeCtx) -> None:
    first = ensure_tags_by_name(make_ctx(), kind=CHAPTER, names=["Cell"])[0]

    again = ensure_tags_by_name(make_ctx(), kind=CHAPTER, names=["CELL ", "cell"])

    assert [tag.id for tag in again] == [first.id]
    assert again[0].name == "Cell"
    assert Tag.objects.count() == 1


def test_the_same_name_is_a_different_tag_per_kind(make_ctx: MakeCtx) -> None:
    chapter = ensure_tags_by_name(make_ctx(), kind=CHAPTER, names=["Genetics"])[0]
    topic = ensure_tags_by_name(make_ctx(), kind=TOPIC, names=["Genetics"])[0]

    assert chapter.id != topic.id


def test_order_is_kept(make_ctx: MakeCtx) -> None:
    ensure_tags_by_name(make_ctx(), kind=TOPIC, names=["Mitosis"])

    tags = ensure_tags_by_name(make_ctx(), kind=TOPIC, names=["Meiosis", "Mitosis", "Cell cycle"])

    assert [tag.name for tag in tags] == ["Meiosis", "Mitosis", "Cell cycle"]
