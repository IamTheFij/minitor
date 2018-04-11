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
                        'We have alerted {alert_count} time(s)'
                    )
                ]
            }
        )

    def test_simple_alert(self, monitor, echo_alert):
        monitor.total_failure_count = 1
        monitor.alert_count = 1
        with patch.object(echo_alert.logger, 'error') as mock_error:
            echo_alert.alert(monitor)
        mock_error.assert_called_once_with(
            'Dummy Monitor has failed 1 time(s)!\n'
            'We have alerted 1 time(s)'
        )
