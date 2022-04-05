from datetime import datetime
from unittest.mock import patch

import pytest

from minitor.main import InvalidMonitorException
from minitor.main import MinitorAlert
from minitor.main import Monitor
from minitor.main import validate_monitor_settings
from tests.util import assert_called_once


class TestMonitor(object):
    @pytest.fixture
    def monitor(self):
        return Monitor(
            {
                "name": "Sample Monitor",
                "command": ["echo", "foo"],
                "alert_down": ["log"],
                "alert_up": ["log"],
                "check_interval": 1,
                "alert_after": 1,
                "alert_every": 1,
            }
        )

    @pytest.mark.parametrize(
        "settings",
        [
            {"alert_after": 0},
            {"alert_every": 0},
            {"check_interval": 0},
            {"alert_after": "invalid"},
            {"alert_every": "invalid"},
            {"check_interval": "invalid"},
        ],
    )
    def test_monitor_invalid_configuration(self, settings):
        with pytest.raises(InvalidMonitorException):
            validate_monitor_settings(settings)

    @pytest.mark.parametrize(
        "alert_after",
        [1, 20],
        ids=lambda arg: "alert_after({})".format(arg),
    )
    @pytest.mark.parametrize(
        "alert_every",
        [-1, 1, 2, 1440],
        ids=lambda arg: "alert_every({})".format(arg),
    )
    def test_monitor_alert_after(self, monitor, alert_after, alert_every):
        monitor.alert_after = alert_after
        monitor.alert_every = alert_every

        # fail a bunch of times before the final failure
        for _ in range(alert_after - 1):
            monitor.failure()

        # this time should raise an alert
        with pytest.raises(MinitorAlert):
            monitor.failure()

    @pytest.mark.parametrize(
        "alert_after",
        [1, 20],
        ids=lambda arg: "alert_after({})".format(arg),
    )
    @pytest.mark.parametrize(
        "alert_every",
        [1, 2, 1440],
        ids=lambda arg: "alert_every({})".format(arg),
    )
    def test_monitor_alert_every(self, monitor, alert_after, alert_every):
        monitor.alert_after = alert_after
        monitor.alert_every = alert_every

        # fail a bunch of times before the final failure
        for _ in range(alert_after - 1):
            monitor.failure()

        # this time should raise an alert
        with pytest.raises(MinitorAlert):
            monitor.failure()

        # fail a bunch more times until the next alert
        for _ in range(alert_every - 1):
            monitor.failure()

        # this failure should alert now
        with pytest.raises(MinitorAlert):
            monitor.failure()

    def test_monitor_alert_every_exponential(self, monitor):
        monitor.alert_after = 1
        monitor.alert_every = -1

        failure_count = 16
        expect_failures_on = {1, 2, 4, 8, 16}

        for i in range(failure_count):
            if i + 1 in expect_failures_on:
                with pytest.raises(MinitorAlert):
                    monitor.failure()
            else:
                monitor.failure()

    @pytest.mark.parametrize("last_check", [None, datetime(2018, 4, 10)])
    def test_monitor_should_check(self, monitor, last_check):
        monitor.last_check = last_check
        assert monitor.should_check()

    def test_monitor_check_fail(self, monitor):
        assert monitor.last_output is None
        with patch.object(monitor, "failure") as mock_failure:
            monitor.command = ["ls", "--not-real"]
            assert not monitor.check()
            assert_called_once(mock_failure)
            assert monitor.last_output is not None

    def test_monitor_check_success(self, monitor):
        assert monitor.last_output is None
        with patch.object(monitor, "success") as mock_success:
            assert monitor.check()
            assert_called_once(mock_success)
            assert monitor.last_output is not None

    @pytest.mark.parametrize("failure_count", [0, 1])
    def test_monitor_success(self, monitor, failure_count):
        monitor.alert_count = 0
        monitor.total_failure_count = failure_count
        assert monitor.last_success is None

        monitor.success()

        assert monitor.alert_count == 0
        assert monitor.last_success is not None
        assert monitor.total_failure_count == 0

    def test_monitor_success_back_up(self, monitor):
        monitor.total_failure_count = 1
        monitor.alert_count = 1

        with pytest.raises(MinitorAlert):
            monitor.success()

        assert monitor.alert_count == 0
        assert monitor.last_success is not None
        assert monitor.total_failure_count == 0
