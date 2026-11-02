"""Questions, their options and their tags."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from core.errors import NotFound
from core.rich_content import Json
from modules.authoring.domain.question_patch import OptionsPlan
from modules.authoring.models import Option, Question, QuestionTag


def insert_question(
    test_id: UUID, section_id: UUID, *, position: int, values: dict[str, object], now: datetime
) -> UUID:
    question = Question.objects.create(
        test_id=test_id,
        section_id=section_id,
        position=position,
        created_at=now,
        updated_at=now,
        **values,
    )
    return question.id


def insert_options(question_id: UUID, contents: Sequence[tuple[Json, bool]]) -> None:
    Option.objects.bulk_create(
        [
            Option(question_id=question_id, position=position, content=content, is_correct=correct)
            for position, (content, correct) in enumerate(contents)
        ]
    )


def update_question(question_id: UUID, values: dict[str, object], *, now: datetime) -> None:
    Question.objects.filter(pk=question_id).update(**values, updated_at=now)


def option_ids(question_id: UUID) -> set[UUID]:
    return set(Option.objects.filter(question_id=question_id).values_list("id", flat=True))


def replace_options(question_id: UUID, plan: OptionsPlan) -> None:
    """Kept options keep their ids; new ones are added; the rest are removed."""
    Option.objects.filter(pk__in=plan.removed).delete()
    kept = [
        Option(
            id=option_id,
            question_id=question_id,
            position=position,
            content=content,
            is_correct=correct,
        )
        for option_id, position, content, correct in plan.rows
        if option_id is not None
    ]
    Option.objects.bulk_update(kept, ["position", "content", "is_correct"])
    Option.objects.bulk_create(
        [
            Option(question_id=question_id, position=position, content=content, is_correct=correct)
            for option_id, position, content, correct in plan.rows
            if option_id is None
        ]
    )


def delete_options(question_id: UUID) -> None:
    Option.objects.filter(question_id=question_id).delete()


def tag_ids(question_id: UUID) -> list[UUID]:
    return list(
        QuestionTag.objects.filter(question_id=question_id).values_list("tag_id", flat=True)
    )


def set_tags(question_id: UUID, *, remove: Sequence[UUID], add: Sequence[UUID]) -> None:
    QuestionTag.objects.filter(question_id=question_id, tag_id__in=remove).delete()
    QuestionTag.objects.bulk_create(
        [QuestionTag(question_id=question_id, tag_id=tag_id) for tag_id in add],
        ignore_conflicts=True,
    )


def delete_questions(question_ids: Sequence[UUID]) -> None:
    Question.objects.filter(pk__in=question_ids).delete()


@dataclass(frozen=True, slots=True)
class CopyTo:
    """Where one copied question goes."""

    source_id: UUID
    test_id: UUID
    section_id: UUID
    position: int


def copy_questions(targets: Sequence[CopyTo], *, now: datetime) -> list[UUID]:
    """Copies with their options and tags, in `targets` order (T-03 Duplicate and Import,
    T-02 Duplicate test). Six queries however many questions."""
    sources = Question.objects.in_bulk([target.source_id for target in targets])
    if len(sources) != len({target.source_id for target in targets}):
        raise NotFound("question")
    copies = [_copy_of(sources[target.source_id], target, now) for target in targets]
    Question.objects.bulk_create(copies)
    new_id = {target.source_id: copy.id for target, copy in zip(targets, copies, strict=True)}
    options = Option.objects.filter(question_id__in=new_id).order_by("question_id", "position")
    Option.objects.bulk_create(
        [
            Option(
                question_id=new_id[o.question_id],
                position=o.position,
                content=o.content,
                is_correct=o.is_correct,
            )
            for o in options
        ]
    )
    tags = QuestionTag.objects.filter(question_id__in=new_id).values_list("question_id", "tag_id")
    QuestionTag.objects.bulk_create(
        [QuestionTag(question_id=new_id[qid], tag_id=tag) for qid, tag in tags]
    )
    return [copy.id for copy in copies]


def _copy_of(source: Question, target: CopyTo, now: datetime) -> Question:
    fields = {
        field.attname: getattr(source, field.attname)
        for field in Question._meta.concrete_fields
        if not field.primary_key
    }
    changes = {
        "test_id": target.test_id,
        "section_id": target.section_id,
        "position": target.position,
        "created_at": now,
        "updated_at": now,
    }
    return Question(**(fields | changes))
