"""Changing a test's settings (T-04): only the parts sent change; a new timing kind goes
through the timing switch first (domain_model.md §3.4, ADR-062)."""

from dataclasses import dataclass, replace

from core.errors import FieldError, FieldsInvalid
from modules.authoring.domain.drafts import Integrity, Marking, TestSettings, Timing
from modules.authoring.domain.settings_rules import (
    GRACE_SECONDS,
    MAX_WARNINGS,
    marks_error,
    range_error,
)
from modules.authoring.domain.structure import TimingSwitch, switch_timing
from modules.authoring.domain.values import TimingKind

DURATION_SECONDS = (60, 24 * 3600)
QUESTION_SECONDS = (5, 3600)


@dataclass(frozen=True, slots=True)
class TimingPatch:
    kind: TimingKind
    # Read only for the kind they belong to
    duration_s: int | None = None
    default_question_s: int | None = None
    allow_return: bool | None = None


@dataclass(frozen=True, slots=True)
class SettingsPatch:
    timing: TimingPatch | None = None
    shuffle_questions: bool | None = None
    shuffle_options: bool | None = None
    marking: Marking | None = None
    integrity: Integrity | None = None


@dataclass(frozen=True, slots=True)
class SettingsChange:
    settings: TestSettings
    # Set when the timing kind changed: what happens to sections
    switch: TimingSwitch | None


def apply_settings_patch(
    current: TestSettings, patch: SettingsPatch, *, section_durations: list[int | None]
) -> SettingsChange:
    _ensure_valid(patch)
    switch = None
    timing = current.timing
    if patch.timing is not None:
        if patch.timing.kind is not timing.kind:
            switch = switch_timing(timing, patch.timing.kind, section_durations=section_durations)
            timing = switch.timing
        timing = _with_values(timing, patch.timing)
    settings = TestSettings(
        timing=timing,
        shuffle_questions=_or(patch.shuffle_questions, current.shuffle_questions),
        shuffle_options=_or(patch.shuffle_options, current.shuffle_options),
        marking=patch.marking or current.marking,
        integrity=patch.integrity or current.integrity,
    )
    return SettingsChange(settings, switch)


def _with_values(timing: Timing, patch: TimingPatch) -> Timing:
    if timing.kind is TimingKind.TOTAL and patch.duration_s is not None:
        return replace(timing, duration_s=patch.duration_s)
    if timing.kind is TimingKind.PER_QUESTION and patch.default_question_s is not None:
        return replace(timing, default_question_s=patch.default_question_s)
    if timing.kind is TimingKind.SECTIONED and patch.allow_return is not None:
        return replace(timing, allow_return=patch.allow_return)
    return timing


def _or(value: bool | None, current: bool) -> bool:
    return current if value is None else value


def _ensure_valid(patch: SettingsPatch) -> None:
    problems: list[FieldError | None] = []
    if patch.timing is not None:
        if patch.timing.duration_s is not None:
            problems.append(
                range_error("settings.timing.duration_s", patch.timing.duration_s, DURATION_SECONDS)
            )
        if patch.timing.default_question_s is not None:
            problems.append(
                range_error(
                    "settings.timing.default_question_s",
                    patch.timing.default_question_s,
                    QUESTION_SECONDS,
                )
            )
    if patch.marking is not None:
        problems.append(
            marks_error("settings.marking.marks", patch.marking.marks, zero_allowed=False)
        )
        problems.append(
            marks_error(
                "settings.marking.negative_marks", patch.marking.negative_marks, zero_allowed=True
            )
        )
    if patch.integrity is not None:
        problems.append(
            range_error("settings.integrity.grace_s", patch.integrity.grace_s, GRACE_SECONDS)
        )
        problems.append(
            range_error(
                "settings.integrity.max_warnings", patch.integrity.max_warnings, MAX_WARNINGS
            )
        )
    errors = [problem for problem in problems if problem is not None]
    if errors:
        raise FieldsInvalid(*errors)
