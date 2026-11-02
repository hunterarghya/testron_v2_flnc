"""Questions, their options and their tags."""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

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


def copy_question(question_id: UUID, *, position: int, now: datetime) -> UUID:
    """A copy right where asked, with its options and tags (T-03 Duplicate, Import)."""
    source = Question.objects.get(pk=question_id)
    fields = {
        field.attname: getattr(source, field.attname)
        for field in Question._meta.concrete_fields
        if not field.primary_key
    }
    copy_id: UUID = Question.objects.create(
        **(fields | {"position": position, "created_at": now, "updated_at": now})
    ).id
    options = Option.objects.filter(question_id=question_id).order_by("position")
    insert_options(copy_id, [(option.content, option.is_correct) for option in options])
    QuestionTag.objects.bulk_create(
        [QuestionTag(question_id=copy_id, tag_id=tag) for tag in tag_ids(question_id)]
    )
    return copy_id
