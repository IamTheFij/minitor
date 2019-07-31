from datetime import datetime
from unittest.mock import patch

import pytest

from minitor.main import Alert
from minitor.main import Monitor
from tests.util import assert_called_once_with


class TestAlert(object):

    @pytest.fixture
    def monitor(self):
        return Monitor({
            'name': 'Dummy Monitor',
            'command': ['echo', 'foo'],
        })

    @pytest.fixture
    def echo_alert(self):
        return Alert(
            'log',
            {
                'command': [
                    'echo', (
                        '{monitor_name} has failed {failure_count} time(s)!\n'
                        'We have alerted {alert_count} time(s)\n'
                        'Last success was {last_success}\n'
                        'Last output was: {last_output}'
                    )
                ]
            }
        )

    @pytest.mark.parametrize(
        'last_success,expected_success',
        [
            (None, 'Never'),
            (datetime(2018, 4, 10), '2018-04-10T00:00:00')
        ]
    )
    def test_simple_alert(
        self,
        monitor,
        echo_alert,
        last_success,
        expected_success
    ):
        monitor.alert_count = 1
        monitor.last_output = 'beep boop'
        monitor.last_success = last_success
        monitor.total_failure_count = 1
        with patch.object(echo_alert._logger, 'error') as mock_error:
            echo_alert.alert('Exception message', monitor)
            assert_called_once_with(
                mock_error,
                'Dummy Monitor has failed 1 time(s)!\n'
                'We have alerted 1 time(s)\n'
                'Last success was ' + expected_success + '\n'
                'Last output was: beep boop'
            )
