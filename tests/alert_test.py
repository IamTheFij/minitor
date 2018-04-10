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
            {'command': ['echo', '{monitor_name} has failed!']}
        )

    def test_simple_alert(self, monitor, echo_alert):
        with patch.object(echo_alert.logger, 'error') as mock_error:
            echo_alert.alert(monitor)
        mock_error.assert_called_once_with('Dummy Monitor has failed!')
