import logging
import subprocess
import sys
from argparse import ArgumentParser
from datetime import datetime
from itertools import chain
from subprocess import CalledProcessError
from subprocess import check_output
from time import sleep

import yamlenv
from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import start_http_server


DEFAULT_METRICS_PORT = 8080
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logging.getLogger(__name__).addHandler(logging.NullHandler())


def read_yaml(path):
    """Loads config from a YAML file with env interpolation"""
    with open(path, 'r') as yaml:
        contents = yaml.read()
        return yamlenv.load(contents)


def validate_monitor_settings(settings):
    """Validates that settings for a Monitor are valid

    Note: Cannot yet validate the Alerts exist from within this class.
    That will be done by Minitor later
    """
    name = settings.get('name')
    if not name:
        raise InvalidMonitorException('Invalid name for monitor')
    if not settings.get('command'):
        raise InvalidMonitorException(
            'Invalid command for monitor {}'.format(name)
        )

    type_assertions = (
        ('check_interval', int),
        ('alert_after', int),
        ('alert_every', int),
    )

    for key, val_type in type_assertions:
        val = settings.get(key)
        if not isinstance(val, val_type):
            raise InvalidMonitorException(
                'Invalid type on {}: {}. Expected {} and found {}'.format(
                    name, key, val_type.__name__, type(val).__name__
                )
            )

    non_zero = (
        'check_interval',
        'alert_after',
    )

    for key in non_zero:
        if settings.get(key) == 0:
            raise InvalidMonitorException(
                'Invalid value for {}: {}. Value cannot be 0'.format(
                    name, key
                )
            )


def maybe_decode(bstr, encoding='utf-8'):
    try:
        return bstr.decode(encoding)
    except TypeError:
        return bstr


def call_output(*popenargs, **kwargs):
    """Similar to check_output, but instead returns output and exception"""
    # So we can capture complete output, redirect sderr to stdout
    kwargs.setdefault('stderr', subprocess.STDOUT)
    output, ex = None, None
    try:
        output = check_output(*popenargs, **kwargs)
    except CalledProcessError as e:
        output, ex = e.output, e

    output = output.rstrip(b'\n')
    return output, ex


class InvalidAlertException(Exception):
    pass


class InvalidMonitorException(Exception):
    pass


class MinitorAlert(Exception):
    def __init__(self, message, monitor):
        super().__init__(message)
        self.monitor = monitor


class Monitor(object):
    """Primary configuration item for Minitor"""

    def __init__(self, config, counter=None, logger=None):
        """Accepts a dictionary of configuration items to override defaults"""
        settings = {
            'alerts': ['log'],
            'check_interval': 30,
            'alert_after': 4,
            'alert_every': -1,
        }
        settings.update(config)
        validate_monitor_settings(settings)

        self.name = settings['name']
        self.command = settings['command']
        self.alert_down = settings.get('alert_down', [])
        if not self.alert_down:
            self.alert_down = settings.get('alerts', [])
        self.alert_up = settings.get('alert_up', [])
        self.check_interval = settings.get('check_interval')
        self.alert_after = settings.get('alert_after')
        self.alert_every = settings.get('alert_every')

        self.alert_count = 0
        self.last_check = None
        self.last_output = None
        self.last_success = None
        self.total_failure_count = 0

        self._counter = counter
        if logger is None:
            self._logger = logging.getLogger(
                '{}({})'.format(self.__class__.__name__, self.name)
            )
        else:
            self._logger = logger.getChild(
                '{}({})'.format(self.__class__.__name__, self.name)
            )

    def _count_check(self, is_success=True, is_alert=False):
        if self._counter is not None:
            self._counter.labels(
                monitor=self.name,
                status=('success' if is_success else 'failure'),
                is_alert=is_alert,
            ).inc()

    def should_check(self):
        """Determines if this Monitor should run it's check command"""
        if not self.last_check:
            return True
        since_last_check = (datetime.now() - self.last_check).total_seconds()
        return since_last_check >= self.check_interval

    def check(self):
        """Returns None if skipped, False if failed, and True if successful

        Will raise an exception if should alert
        """
        if not self.should_check():
            return None

        output, ex = call_output(
            self.command,
            shell=isinstance(self.command, str),
        )
        output = maybe_decode(output)
        self._logger.debug(output)
        self.last_check = datetime.now()
        self.last_output = output

        is_success = None
        try:
            if ex is None:
                is_success = True
                self.success()
            else:
                is_success = False
                self.failure()
        except MinitorAlert:
            self._count_check(is_success=is_success, is_alert=True)
            raise

        self._count_check(is_success=is_success)
        return is_success

    def success(self):
        """Handles success tasks"""
        back_up = None
        if not self.is_up():
            back_up = MinitorAlert(
                '{} check is up again!'.format(self.name),
                self,
            )
        self.total_failure_count = 0
        self.alert_count = 0
        self.last_success = datetime.now()
        if back_up:
            raise back_up

    def failure(self):
        """Handles failure tasks and possibly raises MinitorAlert"""
        self.total_failure_count += 1
        # Ensure we've hit the  minimum number of failures to alert
        if self.total_failure_count < self.alert_after:
            return

        failure_count = (self.total_failure_count - self.alert_after)
        if self.alert_every > 0:
            # Otherwise, we should check against our alert_every
            should_alert = (failure_count % self.alert_every) == 0
        elif self.alert_every == 0:
            # Only alert on the first failure
            should_alert = failure_count == 1
        else:
            should_alert = (failure_count >= (2 ** self.alert_count) - 1)

        if should_alert:
            self.alert_count += 1
            raise MinitorAlert(
                '{} check has failed {} times'.format(
                    self.name, self.total_failure_count
                ),
                self
            )

    def is_up(self):
        """Indicates if the monitor is already alerting failures"""
        return self.alert_count == 0


class Alert(object):
    def __init__(self, name, config, counter=None, logger=None):
        """An alert must be named and have a config dict"""
        self.name = name
        self.command = config.get('command')
        if not self.command:
            raise InvalidAlertException('Invalid alert {}'.format(self.name))

        self._counter = counter
        if logger is None:
            self._logger = logging.getLogger(
                '{}({})'.format(self.__class__.__name__, self.name)
            )
        else:
            self._logger = logger.getChild(
                '{}({})'.format(self.__class__.__name__, self.name)
            )

    def _count_alert(self, monitor):
        """Increments the alert counter"""
        if self._counter is not None:
            self._counter.labels(
                alert=self.name,
                monitor=monitor,
            ).inc()

    def _formated_command(self, **kwargs):
        """Formats command array or string with kwargs from Monitor"""
        if isinstance(self.command, str):
            return self.command.format(**kwargs)
        args = []
        for arg in self.command:
            args.append(arg.format(**kwargs))
        return args

    def _format_datetime(self, dt):
        """Formats a datetime for an alert"""
        if dt is None:
            return 'Never'
        return dt.isoformat()

    def alert(self, message, monitor):
        """Calls the alert command for the provided monitor"""
        self._count_alert(monitor.name)
        output, ex = call_output(
            self._formated_command(
                alert_count=monitor.alert_count,
                alert_message=message,
                failure_count=monitor.total_failure_count,
                last_output=monitor.last_output,
                last_success=self._format_datetime(monitor.last_success),
                monitor_name=monitor.name,
            ),
            shell=isinstance(self.command, str),
        )
        self._logger.error(maybe_decode(output))
        if ex is not None:
            raise ex


class Minitor(object):
    monitors = None
    alerts = None
    state = None
    check_interval = None

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._alert_counter = None
        self._monitor_counter = None
        self._monitor_status_gauge = None

    def _parse_args(self, args=None):
        """Parses command line arguments and returns them"""
        parser = ArgumentParser(description='Minimal monitoring')
        parser.add_argument(
            '--config', '-c',
            dest='config_path',
            default='config.yml',
            help='Path to the config YAML file to use',
        )
        parser.add_argument(
            '--metrics', '-m',
            dest='metrics',
            action='store_true',
            help='Start webserver with metrics',
        )
        parser.add_argument(
            '--metrics-port', '-p',
            dest='metrics_port',
            type=int,
            default=DEFAULT_METRICS_PORT,
            help='Port to use when serving metrics',
        )
        parser.add_argument(
            '--verbose', '-v',
            action='count',
            help=('Adjust log verbosity by increasing arg count. Default log',
                  'level is ERROR. Level increases with each `v`'),
        )
        return parser.parse_args(args)

    def _setup(self, config_path):
        """Load all setup from YAML file at provided path"""
        config = read_yaml(config_path)
        self.check_interval = config.get('check_interval', 30)
        self.monitors = [
            Monitor(
                mon,
                counter=self._monitor_counter,
                logger=self._logger,
            )
            for mon in config.get('monitors', [])
        ]
        # Add default alert for logging
        self.alerts = {
            'log': Alert(
                'log',
                {'command': ['echo', '{alert_message}!']},
                counter=self._alert_counter,
                logger=self._logger,
            )
        }
        self.alerts.update({
            alert_name: Alert(
                alert_name,
                alert,
                counter=self._alert_counter,
                logger=self._logger,
            )
            for alert_name, alert in config.get('alerts', {}).items()
        })

    def _validate_monitors(self):
        """Validates monitors are valid against other config values"""
        for monitor in self.monitors:
            # Validate that the interval is valid
            if monitor.check_interval < self.check_interval:
                raise InvalidMonitorException(
                    'Monitor {} check interval is lower global value {}'.format(
                        monitor.name, self.check_interval
                    )
                )
            # Validate that the the alerts for the monitor exist
            for alert in chain(monitor.alert_down, monitor.alert_up):
                if alert not in self.alerts:
                    raise InvalidMonitorException(
                        'Monitor {} contains an unknown alert: {}'.format(
                            monitor.name, alert
                        )
                    )

    def _init_metrics(self):
        self._alert_counter = Counter(
            'minitor_alert_total',
            'Number of Minitor alerts',
            ['alert', 'monitor'],
        )
        self._monitor_counter = Counter(
            'minitor_check_total',
            'Number of Minitor checks',
            ['monitor', 'status', 'is_alert'],
        )
        self._monitor_status_gauge = Gauge(
            'minitor_monitor_up_count',
            'Currently responsive monitors',
            ['monitor'],
        )

    def _loop(self):
        while True:
            self._check()
            sleep(self.check_interval)

    def _check(self):
        """The main run loop"""
        for monitor in self.monitors:
            try:
                result = monitor.check()
                if result is not None:
                    self._logger.info(
                        '%s: %s',
                        monitor.name,
                        'SUCCESS' if result else 'FAILURE'
                    )
            except MinitorAlert as minitor_alert:
                self._logger.warning(minitor_alert)
                self._handle_minitor_alert(minitor_alert)

            # Track the status of the Monitor
            if self._monitor_status_gauge:
                self._monitor_status_gauge.labels(
                    monitor=monitor.name,
                ).set(int(monitor.is_up()))

    def _handle_minitor_alert(self, minitor_alert):
        """Issues all alerts for a provided monitor"""
        monitor = minitor_alert.monitor
        alerts = monitor.alert_up if monitor.is_up() else monitor.alert_down
        for alert in alerts:
            self.alerts[alert].alert(str(minitor_alert), monitor)

    def _set_log_level(self, verbose):
        """Sets the log level for the class using the provided verbose count"""
        if verbose == 1:
            self._logger.setLevel(logging.WARNING)
        elif verbose == 2:
            self._logger.setLevel(logging.INFO)
        elif verbose >= 3:
            self._logger.setLevel(logging.DEBUG)

    def run(self, args=None):
        """Runs Minitor in a loop"""
        args = self._parse_args(args)

        if args.verbose:
            self._set_log_level(args.verbose)

        if args.metrics:
            self._init_metrics()
            start_http_server(args.metrics_port)

        self._setup(args.config_path)
        self._validate_monitors()

        self._loop()


def main(args=None):
    try:
        Minitor().run(args)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
