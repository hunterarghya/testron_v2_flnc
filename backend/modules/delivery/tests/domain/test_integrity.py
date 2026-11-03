"""The warning decision (domain_model.md §5.8; E-20, E-21; P-06)."""

import pytest

from modules.delivery.domain.integrity import (
    WarningAction,
    WarningDecision,
    decide_warning,
    warning_action,
)
from modules.delivery.domain.values import EndReason


@pytest.mark.parametrize(
    ("count", "action", "counted", "beyond", "expected"),
    [
        # Back within the grace period: recorded, never counted
        (0, "AUTO_SUBMIT", False, False, WarningDecision(False, 0, None)),
        (0, "AUTO_SUBMIT", False, True, WarningDecision(True, 1, None)),
        (1, "AUTO_SUBMIT", False, True, WarningDecision(True, 2, None)),
        # The last allowed warning ends it
        (2, "AUTO_SUBMIT", False, True, WarningDecision(True, 3, EndReason.AUTO_SUBMITTED)),
        (2, "DISQUALIFY", False, True, WarningDecision(True, 3, EndReason.DISQUALIFIED)),
        # The same departure reported again costs nothing more (E-20)
        (2, "AUTO_SUBMIT", True, True, WarningDecision(False, 2, None)),
    ],
)
def test_decide_warning(
    count: int, action: str, counted: bool, beyond: bool, expected: WarningDecision
) -> None:
    assert (
        decide_warning(
            warning_count=count,
            max_warnings=3,
            action=action,
            already_counted=counted,
            beyond_grace=beyond,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("in_progress", "counted", "action"),
    [
        (True, False, WarningAction.NONE),
        (True, True, WarningAction.WARN),
        (False, True, WarningAction.ENDED),
        (False, False, WarningAction.ENDED),
    ],
)
def test_warning_action(in_progress: bool, counted: bool, action: WarningAction) -> None:
    assert warning_action(in_progress=in_progress, counted=counted) is action
