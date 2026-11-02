from typing import Literal, Self
from uuid import UUID

from ninja import Schema
from pydantic import ConfigDict, Field

from modules.authoring.services.commands.rename_tag import RenameTagResult
from modules.authoring.services.queries.list_tags_with_usage import TagUsage
from modules.tagging.public import TagRef

Kind = Literal["CHAPTER", "TOPIC"]


class TagSuggestIn(Schema):
    model_config = ConfigDict(extra="forbid")

    kind: Kind
    q: str = Field(default="", max_length=160)


class TagFilterIn(Schema):
    model_config = ConfigDict(extra="forbid")

    kind: Kind | None = None
    q: str | None = Field(default=None, max_length=160)


class TagRenameIn(Schema):
    model_config = ConfigDict(extra="forbid")

    # Cleaned and checked (1 to 80 characters) by the use case, reported against `name`
    name: str = Field(max_length=160)
    merge: bool = False


class TagOut(Schema):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    kind: Kind
    name: str

    @classmethod
    def from_ref(cls, tag: TagRef) -> Self:
        return cls(id=tag.id, kind=tag.kind.value, name=tag.name)


class TagUsageOut(TagOut):
    question_count: int
    test_count: int

    @classmethod
    def from_usage(cls, usage: TagUsage) -> Self:
        return cls(
            id=usage.tag.id,
            kind=usage.tag.kind.value,
            name=usage.tag.name,
            question_count=usage.question_count,
            test_count=usage.test_count,
        )


class TagRenameOut(Schema):
    model_config = ConfigDict(extra="forbid")

    tag: TagOut
    merged_from: UUID | None

    @classmethod
    def from_result(cls, result: RenameTagResult) -> Self:
        return cls(tag=TagOut.from_ref(result.tag), merged_from=result.merged_from)


class TagDeleteOut(Schema):
    model_config = ConfigDict(extra="forbid")

    removed_from_questions: int
