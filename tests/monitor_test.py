import pytest

from minitor.main import InvalidMonitorException
from minitor.main import MinitorAlert
from minitor.main import Monitor
from minitor.main import validate_monitor_settings


class TestMonitor(object):

    @pytest.fixture
    def monitor(self):
        return Monitor({
            'name': 'SampleMonitor',
            'command': ['echo', 'foo'],
        })

    @pytest.mark.parametrize('settings', [
        {'alert_after': 0},
        {'alert_every': 0},
        {'check_interval': 0},
        {'alert_after': 'invalid'},
        {'alert_every': 'invalid'},
        {'check_interval': 'invalid'},
    ])
    def test_monitor_invalid_configuration(self, settings):
        with pytest.raises(InvalidMonitorException):
            validate_monitor_settings(settings)

    @pytest.mark.parametrize(
        'alert_after',
        [1, 20],
        ids=lambda arg: 'alert_after({})'.format(arg),
    )
    @pytest.mark.parametrize(
        'alert_every',
        [-1, 1, 2, 1440],
        ids=lambda arg: 'alert_every({})'.format(arg),
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
        'alert_after',
        [1, 20],
        ids=lambda arg: 'alert_after({})'.format(arg),
    )
    @pytest.mark.parametrize(
        'alert_every',
        [1, 2, 1440],
        ids=lambda arg: 'alert_every({})'.format(arg),
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
