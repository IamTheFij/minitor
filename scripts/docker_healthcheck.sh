#! /bin/bash

#################
# docker_healthcheck.sh
#
# Returns the results of a Docker Healthcheck for a container
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
    echo "Will return results of healthcheck for continer with provided name"
    exit 1
fi

container_id=$(get_container_id $container_name)
if [ -z "$container_id" ]; then
    echo "ERROR: Could not find container with name: $container_name"
    exit 1
fi
health=$(inspect_container $container_id | jq -r '.State.Health.Status')

case $health in
    "null")
        echo "No healthcheck results"
        ;;
    "starting|healthy")
        echo "Status: '$health'"
        ;;
    *)
        echo "Status: '$health'"
        exit 1
esac
