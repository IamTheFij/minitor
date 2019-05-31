# Docker Checks

A sample docker-compose example that uses the bundled shell scripts to monitor the health of other Docker containers.

## Security note

Exposing `/var/run/docker.sock` comes at a risk. Please be careful when doing this. If someone is able to take over your Minitor container, they will then essentially have root access to your whole host. To minimize risk, be wary of exposing Minitor to the public internet when using a configuration like this.
