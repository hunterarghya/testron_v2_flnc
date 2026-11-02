from uuid import UUID

import pytest

from core.errors import FieldsInvalid
from modules.tagging.domain.names import TagKind, TagRef, display_tag_name, normalize_tag_name
from modules.tagging.domain.suggestions import MAX_SUGGESTIONS, rank_suggestions

ZWJ = chr(0x200D)
RIGHT_TO_LEFT_OVERRIDE = chr(0x202E)


# domain_model.md §4.1: "Cell", "cell " and "CELL" are one tag (testing_strategy.md: ≥ 10 rows)
@pytest.mark.parametrize(
    ("raw", "normalized", "display"),
    [
        ("Cell", "cell", "Cell"),
        ("cell ", "cell", "cell"),
        ("CELL", "cell", "CELL"),
        ("  Cell   Biology ", "cell biology", "Cell Biology"),
        ("Cell\tBiology", "cell biology", "Cell Biology"),
        ("কোষ", "কোষ", "কোষ"),
        ("  কোষ   বিভাজন ", "কোষ বিভাজন", "কোষ বিভাজন"),
        (f"র{ZWJ}্যাব", f"র{ZWJ}্যাব", f"র{ZWJ}্যাব"),
        (f"Mitosis{RIGHT_TO_LEFT_OVERRIDE}", "mitosis", "Mitosis"),
        ("Straße", "strasse", "Straße"),
        ("DNA-Replication", "dna-replication", "DNA-Replication"),
    ],
    ids=[
        "title-case",
        "trailing-space",
        "upper-case",
        "inner-spaces",
        "tab",
        "bengali",
        "bengali-spaces",
        "bengali-joiner-kept",
        "bidi-removed",
        "german-sharp-s",
        "punctuation-kept",
    ],
)
def test_tag_names(raw: str, normalized: str, display: str) -> None:
    assert normalize_tag_name(raw) == normalized
    assert display_tag_name(raw) == display


@pytest.mark.parametrize("raw", ["", "   ", "x" * 81])
def test_empty_or_long_names_are_refused(raw: str) -> None:
    with pytest.raises(FieldsInvalid):
        display_tag_name(raw)


def tag(number: int, name: str) -> TagRef:
    return TagRef(id=UUID(int=number), kind=TagKind.CHAPTER, name=name)


CELL, CEREBRAL, NUCLEUS, CELLULAR = (
    tag(1, "Cell"),
    tag(2, "Cerebral system"),
    tag(3, "Nucleus"),
    tag(4, "Intercellular"),
)


def test_prefix_matches_come_before_contains_matches() -> None:
    ranked = rank_suggestions([CELLULAR, NUCLEUS, CEREBRAL, CELL], "ce", usage={})

    assert ranked == [CELL, CEREBRAL, CELLULAR]


def test_more_used_tags_come_first_within_each_group() -> None:
    ranked = rank_suggestions([CELL, CEREBRAL], "ce", usage={CEREBRAL.id: 5, CELL.id: 1})

    assert ranked == [CEREBRAL, CELL]


def test_typing_is_matched_ignoring_case() -> None:
    assert rank_suggestions([CELL], "  CE", usage={}) == [CELL]


def test_at_most_eight_suggestions() -> None:
    many = [tag(number, f"Chapter {number}") for number in range(20)]

    assert len(rank_suggestions(many, "ch", usage={})) == MAX_SUGGESTIONS
