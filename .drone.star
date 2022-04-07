# Build pipelines
def main(ctx):
    pipelines = []

    # Run tests
    pipelines += run_tests()

    # Add pypi push pipeline
    pipelines += push_to_pypi(ctx)

    # Add docker push pipelines
    pipelines += push_to_docker(ctx)

    return pipelines


# Return workspace in the container
def get_workspace():
    return {
        "base": "/app",
        "path": ".",
    }


# Builds a list of all test pipelines to be executed
def run_tests():
    return [{
        "kind": "pipeline",
        "name": "tests",
        "workspace": get_workspace(),
        "steps": [
            tox_step("python:3.7"),
            tox_step("python:3.8"),
            tox_step("python:3.9"),
            tox_step("python:3.10"),
            tox_step("python:3"),
            # tox_step("pypy:3.9", "pypy3", "pypy3"),
            # tox_step("pypy:3", "pypy3", "pypy3"),
            notify_step(),
        ],
    }]


# Builds a single python test step
def tox_step(docker_tag, python_cmd="python", tox_env="py3"):
    return {
        "name": "test {}".format(docker_tag.replace(":", "")),
        "image": docker_tag,
        "environment": {
            "TOXENV": tox_env,
        },
        "commands": [
            "{} -V".format(python_cmd),
            "pip install tox",
            "tox",
        ],
    }


# Builds a notify step that will notify when the previous step changes
def notify_step():
    return {
        "name": "notify",
        "image": "drillster/drone-email",
        "settings": {
            "host": {
                "from_secret": "SMTP_HOST",
            },
            "username": {
                "from_secret": "SMTP_USER",
            },
            "password": {
                "from_secret": "SMTP_PASS",
            },
            "from": "drone@iamthefij.com",
        },
        "when": {
            "status": [
                "changed",
                "failure",
            ],
        },
    }


# Push package to pypi
def push_to_pypi(ctx):
    return [{
        "kind": "pipeline",
        "name": "deploy to pypi",
        "depends_on": ["tests"],
        "workspace": get_workspace(),
        "trigger": {
            "event": ["tag"],
            "ref": [
                "refs/heads/master",
                "refs/tags/v*",
            ],
        },
        "steps": [
            {
                "name": "push to test pypi",
                "image": "python:3",
                "environment": {
                    "TWINE_USERNAME": {
                        "from_secret": "PYPI_USERNAME",
                    },
                    "TWINE_PASSWORD": {
                        "from_secret": "TEST_PYPI_PASSWORD",
                    },
                },
                "commands": ["make upload-test"],
            },
            {
                "name": "push to pypi",
                "image": "python:3",
                "environment": {
                    "TWINE_USERNAME": {
                        "from_secret": "PYPI_USERNAME",
                    },
                    "TWINE_PASSWORD": {
                        "from_secret": "PYPI_PASSWORD",
                    },
                },
                "commands": ["make upload"],
                "when": {
                    "event": ["tag"],
                },
            },
            notify_step(),
        ]
    }]


# Build and push docker image
def push_docker_step(tag_suffix, arch, repo):
    return {
        "name": "push {}".format(tag_suffix),
        "image": "plugins/docker",
        "settings": {
            "repo": "iamthefij/minitor",
            "auto_tag": True,
            "auto_tag_suffix": tag_suffix,
            "username": {
                "from_secret": "docker_username",
            },
            "password": {
                "from_secret": "docker_password",
            },
            "build_args": [
                "ARCH={}".format(arch),
                "REPO={}".format(repo),
            ],
        },
    }


# Builds a pipeline to push to docker
def push_to_docker(ctx):
    return [{
        "kind": "pipeline",
        "name": "push to docker",
        "depends_on": ["tests"],
        "workspace": get_workspace(),
        "trigger": {
            "event": ["tag", "push"],
            "ref": [
                "refs/heads/master",
                "refs/tags/v*",
            ],
        },
        "steps": [
            {
                "name": "get qemu",
                "image": "busybox",
                "commands": ["sh ./get_qemu.sh x86_64 arm aarch64"],
            },
            push_docker_step("linux-amd64", "x86_64", "library"),
            push_docker_step("linux-arm", "arm", "arm32v6"),
            push_docker_step("linux-arm64", "aarch64", "arm64v8"),
            {
                "name": "publish manifest",
                "image": "plugins/manifest",
                "settings": {
                    "spec": "manifest.tmpl",
                    "auto_tag": True,
                    "ignore_missing": True,
                    "username": {
                        "from_secret": "docker_username",
                    },
                    "password": {
                        "from_secret": "docker_password",
                    },
                }
            },
            notify_step(),
        ],
    }]


# vim: ft=python
