from collections.abc import Sequence
from typing import cast
from uuid import UUID

from core.context import Ctx
from core.rich_content import Profile, plain_text
from modules.authoring.domain.document import QuestionView, TagLabel
from modules.authoring.domain.question_patch import (
    OptionInput,
    QuestionChanges,
    ensure_changes_valid,
    plan_options,
)
from modules.authoring.domain.values import QuestionType
from modules.authoring.repositories import questions, tests_table
from modules.authoring.services.editing import EditResult, edit, read_document, rich
from modules.tagging import public as tagging

_COLUMNS = (
    "marks_override",
    "negative_marks_override",
    "time_override_s",
    "numeric_answer",
    "numeric_tolerance",
)


def update_question(
    ctx: Ctx, *, question_id: UUID, revision: int, changes: QuestionChanges
) -> EditResult[UUID]:
    """Save one question as a whole: the editor's autosave (api_contract.md §2.5).

    Options replace the stored list (kept ids stay). Switching to numerical removes the
    options; leaving numerical clears the answer value. MCQ <-> MSQ keeps everything, even a
    second correct option (that becomes a problem, not a silent change; domain_model.md §3.4
    invariant 3). Tags come by name and are created as needed (§4.1).
    """
    test_id = tests_table.owning_test_of_question(question_id)
    checked = _checked_content(changes)

    def change() -> UUID:
        current = read_document(test_id).question(question_id)
        final_type = checked.get("type", current.type)
        ensure_changes_valid(final_type, checked)
        questions.update_question(question_id, _columns(checked, final_type), now=ctx.now)
        _save_options(question_id, checked, final_type)
        _save_tags(ctx, current, checked)
        return question_id

    return edit(ctx, test_id, revision=revision, change=change)


def _checked_content(changes: QuestionChanges) -> QuestionChanges:
    """The rich fields validated and normalized (stem and solution: full; options: compact)."""
    checked = QuestionChanges(**changes)
    if "stem" in changes:
        checked["stem"] = rich("stem", changes["stem"])
    if changes.get("solution") is not None:
        checked["solution"] = rich("solution", changes["solution"])
    if "options" in changes:
        checked["options"] = [
            OptionInput(
                o.id, rich(f"options.{i}.content", o.content, Profile.COMPACT), o.is_correct
            )
            for i, o in enumerate(changes["options"])
        ]
    return checked


def _columns(changes: QuestionChanges, final_type: QuestionType) -> dict[str, object]:
    sent = cast("dict[str, object]", changes)
    values = {name: sent[name] for name in _COLUMNS if name in sent}
    values["type"] = final_type.value
    if "stem" in changes:
        values["stem"] = changes["stem"]
        values["search_text"] = plain_text(changes["stem"])
    if "solution" in changes:
        values["solution"] = changes["solution"]
    if final_type is not QuestionType.NUMERICAL:
        values.update(numeric_answer=None, numeric_tolerance=0)
    return values


def _save_options(question_id: UUID, changes: QuestionChanges, final_type: QuestionType) -> None:
    if final_type is QuestionType.NUMERICAL:
        questions.delete_options(question_id)
    elif "options" in changes:
        questions.replace_options(
            question_id, plan_options(questions.option_ids(question_id), changes["options"])
        )


def _save_tags(ctx: Ctx, current: QuestionView, changes: QuestionChanges) -> None:
    if "chapter_tags" in changes:
        _replace_tags(
            ctx, current.id, current.chapter_tags, changes["chapter_tags"], tagging.TagKind.CHAPTER
        )
    if "topic_tags" in changes:
        _replace_tags(
            ctx, current.id, current.topic_tags, changes["topic_tags"], tagging.TagKind.TOPIC
        )


def _replace_tags(
    ctx: Ctx, question_id: UUID, held: Sequence[TagLabel], names: list[str], kind: tagging.TagKind
) -> None:
    wanted = tagging.ensure_tags_by_name(ctx, kind=kind, names=names)
    questions.set_tags(
        question_id, remove=[label.id for label in held], add=[tag.id for tag in wanted]
    )
