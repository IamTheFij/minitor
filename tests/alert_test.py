from datetime import datetime
from unittest.mock import patch

import pytest

from minitor.main import Alert
from minitor.main import Monitor


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
                        'Last success was {last_success}'
                    )
                ]
            }
        )

    @pytest.mark.parametrize(
        'last_success',
        [
            (None, 'Never'),
            (datetime(2018, 4, 10), '2018-04-10T00:00:00')
        ]
    )
    def test_simple_alert(self, monitor, echo_alert, last_success):
        monitor.total_failure_count = 1
        monitor.alert_count = 1
        monitor.last_success = last_success[0]
        with patch.object(echo_alert.logger, 'error') as mock_error:
            echo_alert.alert(monitor)
        mock_error.assert_called_once_with(
            'Dummy Monitor has failed 1 time(s)!\n'
            'We have alerted 1 time(s)\n'
            'Last success was ' + last_success[1]
        )
