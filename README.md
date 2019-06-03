# minitor

A minimal monitoring system

## What does it do?

Minitor accepts a YAML configuration file with a set of commands to run and a set of alerts to execute when those commands fail. It is designed to be as simple as possible and relies on other command line tools to do checks and issue alerts.

## But why?

I'm running a few small services and found Sensu, Consul, Nagios, etc. to all be far too complicated for my usecase.

## So how do I use it?

### Running

Install and execute with:

```
pip install minitor
minitor
```

If locally developing you can use:

```
make run
```

It will read the contents of `config.yml` and begin its loop. You could also run it directly and provide a new config file via the `--config` argument.


#### Docker

You can pull this repository directly from Docker:

`docker pull iamthefij/minitor`

The Docker image uses a default `config.yml` that is copied from `sample-config.yml`. This won't really do anything for you, so when you run the Docker image, you should supply your own `config.yml` file:

`docker run -v $PWD/config.yml:/app/config.yml iamthefij/minitor`

## Configuring

In this repo, you can explore the `sample-config.yml` file for an example, but the general structure is as follows. It should be noted that environment variable interpolation happens on load of the YAML file.

The global configurations are:

|key|value|
|---|---|
|`check_interval`|Maximum frequency to run checks for each monitor|
|`monitors`|List of all monitors. Detailed description below|
|`alerts`|List of all alerts. Detailed description below|

### Monitors

All monitors should be listed under `monitors`.

Each monitor allows the following configuration:

|key|value|
|---|---|
|`name`|Name of the monitor running. This will show up in messages and logs.|
|`command`|Specifies the command that should be executed, either in exec or shell form. This command's exit value will determine whether the check is successful|
|`alert_down`|A list of Alerts to be triggered when the monitor is in a "down" state|
|`alert_up`|A list of Alerts to be triggered when the monitor moves to an "up" state|
|`check_interval`|The interval at which this monitor should be checked. This must be greater than the global `check_interval` value|
|`alert_after`|Allows specifying the number of failed checks before an alert should be triggered|
|`alert_every`|Allows specifying how often an alert should be retriggered. There are a few magic numbers here. Defaults to `-1` for an exponential backoff. Setting to `0` disables re-alerting. Positive values will allow retriggering after the specified number of checks|

### Alerts

Alerts exist as objects keyed under `alerts`. Their key should be the name of the Alert. This is used in your monitor setup in `alert_down` and `alert_up`.

Eachy alert allows the following configuration:

|key|value|
|---|---|
|`command`|Specifies the command that should be executed, either in exec or shell form. This is the command that will be run when the alert is executed. This can be templated with environment variables or the variables shown in the table below|

Also, when alerts are executed, they will be passed through Python's format function with arguments for some attributes of the Monitor. The following monitor specific variables can be referenced using Python formatting syntax:

|token|value|
|---|---|
|`{alert_count}`|Number of times this monitor has alerted|
|`{alert_message}`|The exception message that was raised|
|`{failure_count}`|The total number of sequential failed checks for this monitor|
|`{last_output}`|The last returned value from the check command to either stderr or stdout|
|`{last_success}`|The ISO datetime of the last successful check|
|`{monitor_name}`|The name of the monitor that failed and triggered the alert|

### Metrics

As of v0.3.0, Minitor supports exporting metrics for [Prometheus](https://prometheus.io/). Prometheus is an open source tool for reading and querying metrics from different sources. Combined with another tool, [Grafana](https://grafana.com/), it allows building of charts and dashboards. You could also opt to just use Minitor to log check results, and instead do your alerting with Grafana.

It is also possible to use the metrics endpoint for monitoring Minitor itself! This allows setting up multiple instances of Minitor on different servers and have them monitor each-other so that you can detect a minitor outage.

To run minitor with metrics, use the `--metrics` (or `-m`) flag. The metrics will be served on port `8080` by default, though it can be overriden using `--metrics-port` (or `-p`)

```
minitor --metrics
# or
minitor --metrics --metrics-port 3000
```

## Contributing

Whether you're looking to submit a patch or just tell me I broke something, you can contribute through the Github mirror and I can merge PRs back to the source repository.

Primary Repo: https://git.iamthefij.com/iamthefij/minitor.git

Github Mirror: https://github.com/IamTheFij/minitor.git
