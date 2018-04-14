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

### Configuring

In this repo, you can explore the `sample-config.yml` file for an example, but the general structure is as follows. It should be noted that environment variable interpolation happens on load of the YAML file. Also, when alerts are executed, they will be passed through Python's format function with arguments for some attributes of the Monitor. Currently this is limited to `{monitor_name}`.

## Contributing

Whether you're looking to submit a patch or just tell me I broke something, you can contribute through the Github mirror and I can merge PRs back to the source repository.

Primary Repo: https://git.iamthefij.com/iamthefij/minitor.git

Github Mirror: https://github.com/IamTheFij/minitor.git
