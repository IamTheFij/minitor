import os
from unittest.mock import patch

from minitor.main import call_output
from minitor.main import Minitor


class TestMinitor(object):

    def test_call_output(self):
        # valid command should have result and no exception
        output, ex = call_output(['echo', 'test'])
        assert output == b'test'
        assert ex is None

        output, ex = call_output(['ls', '--not-a-real-flag'])
        assert output.startswith(b'ls: ')
        assert ex is not None

    def test_run(self):
        """Doesn't really check much, but a simple integration sanity test"""
        test_loop_count = 5
        os.environ.update({
            'MAILGUN_API_KEY': 'test-mg-key',
            'AVAILABLE_NUMBER': '555-555-5050',
            'MY_PHONE': '555-555-0505',
            'ACCOUNT_SID': 'test-account-id',
            'ACCOUNT_TOKEN': 'test-account-token',
        })
        args = '--config ./sample-config.yml'.split(' ')
        minitor = Minitor()
        with patch.object(minitor, '_loop'):
            minitor.run(args)
            # Skip the loop, but run a single check
            for _ in range(test_loop_count):
                minitor._check()
