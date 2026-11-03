"""The live monitor's statuses and filters (T-10)."""

import pytest

from modules.delivery.domain.monitor import MonitorFilter, MonitorStatus, is_shown, monitor_status
from modules.delivery.domain.values import AttemptStatus, EndReason

S = MonitorStatus


@pytest.mark.parametrize(
    ("status", "reason", "expected"),
    [
        (None, None, S.NOT_STARTED),
        (AttemptStatus.IN_PROGRESS, None, S.IN_PROGRESS),
        (AttemptStatus.ENDED, EndReason.TIMED_OUT, S.TIMED_OUT),
        (AttemptStatus.ENDED, EndReason.DISQUALIFIED, S.DISQUALIFIED),
    ],
)
def test_monitor_status(
    status: AttemptStatus | None, reason: EndReason | None, expected: MonitorStatus
) -> None:
    assert monitor_status(status, reason) is expected


@pytest.mark.parametrize(
    ("chosen", "status", "warnings", "shown"),
    [
        (MonitorFilter.ALL, S.SUBMITTED, 0, True),
        (MonitorFilter.IN_PROGRESS, S.IN_PROGRESS, 0, True),
        (MonitorFilter.IN_PROGRESS, S.SUBMITTED, 0, False),
        (MonitorFilter.NOT_STARTED, S.NOT_STARTED, 0, True),
        (MonitorFilter.ENDED, S.AUTO_SUBMITTED, 0, True),
        (MonitorFilter.ENDED, S.IN_PROGRESS, 0, False),
        (MonitorFilter.FLAGGED, S.IN_PROGRESS, 2, True),
        (MonitorFilter.FLAGGED, S.SUBMITTED, 0, False),
    ],
)
def test_filters(chosen: MonitorFilter, status: MonitorStatus, warnings: int, shown: bool) -> None:
    assert is_shown(chosen, status, warnings=warnings) is shown
