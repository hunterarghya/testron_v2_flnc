"""Settings patches and checks (domain_model.md §3.5, api_contract.md §2.6)."""

from dataclasses import replace

import pytest

from core.errors import FieldsInvalid
from modules.assignments.domain.assignment import Settings, SettingsPatch, checked_settings
from modules.assignments.domain.settings import Integrity, Publication
from modules.assignments.domain.values import PublicationMode, WindowKind
from modules.assignments.domain.window import Window

SETTINGS = Settings(
    title="Cell Biology",
    window=Window(WindowKind.OPEN),
    requires_activation=False,
    integrity=Integrity(grace_s=5, max_warnings=3, action="AUTO_SUBMIT"),
    publication=Publication(),
)


def test_an_empty_patch_changes_nothing() -> None:
    assert SettingsPatch().changed_fields() == []
    assert SettingsPatch().applied_to(SETTINGS) == SETTINGS


def test_a_patch_names_and_applies_what_it_sets() -> None:
    window = Window(WindowKind.MANUAL)
    patch = SettingsPatch(
        title="New",
        window=window,
        requires_activation=True,
        integrity=Integrity(0, 1, "DISQUALIFY"),
        publication=Publication(mode=PublicationMode.AUTO_IMMEDIATE),
    )

    assert patch.changed_fields() == ["title", "window", "gate", "integrity", "publication"]
    applied = patch.applied_to(SETTINGS)
    assert (applied.title, applied.window, applied.requires_activation) == ("New", window, True)


def test_a_false_gate_still_counts_as_a_change() -> None:
    assert SettingsPatch(requires_activation=False).changed_fields() == ["gate"]


def test_checked_settings_cleans_the_title() -> None:
    assert checked_settings(replace(SETTINGS, title="  Cell   Biology ")).title == "Cell Biology"


@pytest.mark.parametrize(
    "settings",
    [
        replace(SETTINGS, title="   "),
        replace(SETTINGS, publication=Publication(mode=PublicationMode.AUTO_DELAYED)),
        replace(SETTINGS, integrity=Integrity(99, 3, "AUTO_SUBMIT")),
    ],
)
def test_checked_settings_refuses_bad_values(settings: Settings) -> None:
    with pytest.raises(FieldsInvalid):
        checked_settings(settings)
