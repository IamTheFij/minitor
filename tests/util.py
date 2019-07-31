from unittest import mock


def assert_called_once(mocked):
    """Safe convenient methods for mock asserts"""
    assert mocked.call_count == 1


def assert_called_once_with(mocked, *args, **kwargs):
    """Safe convenient methods for mock asserts"""
    assert_called_once(mocked)
    assert mocked.call_args == mock.call(*args, **kwargs)
