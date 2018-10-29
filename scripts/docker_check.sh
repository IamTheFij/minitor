#! /bin/bash
set -e

#################
# docker_check.sh
#
# Checks the most recent state exit code of a Docker container
#################

container_name=$1

# Returns caintainer ID for a given container name
function get_container_id {
    local container_name=$1
    curl --unix-socket /var/run/docker.sock 'http://localhost/containers/json?all=1' 2>/dev/null \
        | jq -r ".[] | {Id, Name: .Names[]} | select(.Name == \"/${container_name}\") | .Id"
}

# Returns container JSON
function inspect_container {
    local container_id=$1
    curl --unix-socket /var/run/docker.sock http://localhost/containers/$container_id/json 2>/dev/null
}

if [ -z "$container_name" ]; then
    echo "Usage: $0 container_name"
    echo "Will exit with the last status code of continer with provided name"
    exit 1
fi

container_id=$(get_container_id $container_name)
if [ -z "$container_id" ]; then
    echo "ERROR: Could not find container with name: $container_name"
    exit 1
fi
exit_code=$(inspect_container $container_id | jq -r .State.ExitCode)

exit $exit_code
