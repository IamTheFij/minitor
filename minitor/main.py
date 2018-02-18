import logging
import sys
from argparse import ArgumentParser
from datetime import datetime
from os import environ
from subprocess import CalledProcessError
from subprocess import call
from subprocess import check_call
from time import sleep

import yamlenv


logging.basicConfig(level=logging.INFO)
logging.getLogger(__name__).addHandler(logging.NullHandler())


def read_yaml(path):
    """Loads config from a YAML file with env interpolation"""
    with open(path, 'r') as yaml:
        contents = yaml.read()
        return yamlenv.load(contents)


class InvalidAlertException(Exception):
    pass


class InvalidMonitorException(Exception):
    pass


class MinitorAlert(Exception):
    pass


class Monitor(object):
    """Primary configuration item for Minitor"""
    def __init__(self, config):
        """Accepts a dictionary of configuration items to override defaults"""
        settings = {
            'alerts': [ 'log' ],
            'check_interval': 30,
            'alert_after': 4,
            'alert_every': -1,
        }
        settings.update(config)
        self.validate_settings(settings)

        self.name = settings['name']
        self.command = settings['command']
        self.alerts = settings.get('alerts', [])
        self.check_interval = settings.get('check_interval')
        self.alert_after = settings.get('alert_after')
        self.alert_every = settings.get('alert_every')

        self.last_check = None
        self.failure_count = 0
        self.alert_count = 0

    def validate_settings(self, settings):
        """Validates that settings for this Monitor are valid

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
                    'Invalid type on {} {}. Expected {} and found {}'.format(
                        name, key, val_type.__name__, type(val).__name__
                    )
                )

    def should_check(self):
        """Determines if this Monitor should run it's check command"""
        if not self.last_check:
            return True
        since_last_check = (datetime.now()-self.last_check).total_seconds()
        return since_last_check >= self.check_interval

    def check(self):
        """Returns None if skipped, False if failed, and True if successful

        Will raise an exception if should alert
        """
        if not self.should_check():
            return None
        result = call(self.command, shell=isinstance(self.command, str))
        self.last_check = datetime.now()
        if result == 0:
            self.success()
            return True
        else:
            self.failure()
            return False

    def success(self):
        """Handles success tasks"""
        self.failure_count = 0
        self.alert_count = 0

    def failure(self):
        """Handles failure tasks and possibly raises MinitorAlert"""
        self.failure_count += 1
        if self.failure_count < self.alert_after:
            return
        if self.alert_every >= 0:
            failure_interval = (self.failure_count % self.alert_every) == 0
        else:
            failure_interval = (
                (self.failure_count - self.alert_after) >=
                (2 ** self.alert_count)
            )
        if failure_interval:
            self.alert_count += 1
            raise MinitorAlert('{} check has failed {} times'.format(
                self.name, self.failure_count
            ))


class Alert(object):
    def __init__(self, name, config):
        """An alert must be named and have a config dict"""
        self.name = name
        self.command = config.get('command')
        if not self.command:
            raise InvalidAlertException('Invalid alert {}'.format(self.name))

    def _formated_command(self, **kwargs):
        """Formats command array or string with kwargs from Monitor"""
        if isinstance(self.command, str):
            return self.command.format(**kwargs)
        args = []
        for arg in self.command:
            args.append(arg.format(**kwargs))
        return args

    def alert(self, monitor):
        """Calls the alert command for the provided monitor"""
        check_call(
            self._formated_command(monitor_name=monitor.name),
            shell=isinstance(self.command, str),
        )


class Minitor(object):
    monitors = None
    alerts = None
    state = None
    check_interval = None

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def setup(self, config_path):
        """Load all setup from YAML file at provided path"""
        config = read_yaml(config_path)
        self.check_interval = config.get('check_interval', 30)
        self.monitors = [Monitor(mon) for mon in config.get('monitors', [])]
        # Add default alert for logging
        self.alerts = {
            'log': Alert(
                'log',
                {'command': ['echo', '{monitor_name} has failed!']}
            )
        }
        self.alerts.update({
            alert_name: Alert(alert_name, alert)
            for alert_name, alert in config.get('alerts', {}).items()
        })

    def validate_monitors(self):
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
            for alert in monitor.alerts:
                if alert not in self.alerts:
                    raise InvalidMonitorException(
                        'Monitor {} contains an unknown alert: {}'.format(
                            monitor.name, alert
                        )
                    )

    def alert_for_monitor(self, monitor):
        """Issues all alerts for a provided monitor"""
        for alert in monitor.alerts:
            self.alerts[alert].alert(monitor)

    def parse_args(self):
        """Parses command line arguments and returns them"""
        parser = ArgumentParser(description='Minimal monitoring')
        parser.add_argument(
            '--config', '-c',
            dest='config_path',
            default='config.yml',
            help='Path to the config YAML file to use'
        )
        return parser.parse_args()

    def run(self):
        """Runs Minitor in a loop"""
        args = self.parse_args()
        self.setup(args.config_path)
        self.validate_monitors()

        while True:
            for monitor in self.monitors:
                try:
                    result = monitor.check()
                    if result is not None:
                        self.logger.info('%s: %s',
                            monitor.name,
                            'SUCCESS' if result else 'FAILURE'
                        )
                except MinitorAlert as minitor_alert:
                    self.logger.warn(minitor_alert)
                    self.alert_for_monitor(monitor)

            sleep(self.check_interval)


def main():
    try:
        Minitor().run()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
