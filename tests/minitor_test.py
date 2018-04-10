from minitor.main import call_output


class TestMinitor(object):

    def test_call_output(self):
        # valid command should have result and no exception
        output, ex = call_output(['echo', 'test'])
        assert output == b'test'
        assert ex is None

        output, ex = call_output(['ls', '--not-a-real-flag'])
        assert output.startswith(b'ls: illegal option')
        assert ex is not None
