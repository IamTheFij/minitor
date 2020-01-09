# Build pipelines
def main(ctx):
    pipelines = []

    # Run tests
    test_pipelines = build_test_pipelines()
    pipelines += test_pipelines

    # Wait for all tests to complete
    pipelines.append(wait_for_all_tests(test_pipelines))

    # Add pypi push pipeline
    pipelines.append(push_to_pypi(ctx))

    # Add docker push pipelines
    pipelines += docker_pipelines()

    return pipelines


# Return workspace in the container
def get_workspace():
    return {
        "base": "/app",
        "path": ".",
    }


# Builds a list of all test pipelines to be executed
def build_test_pipelines():
    return [
        test("python:3.5"),
        test("python:3.6"),
        test("python:3.7"),
        test("python:3.8"),
        test("python:3"),
        test("pypy:3.6", "pypy3", "pypy3"),
        test("pypy:3", "pypy3", "pypy3"),
    ]


# Waits for the completion of all test pipelines
def wait_for_all_tests(test_pipelines):
    depends_on = []
    for pipeline in test_pipelines:
        depends_on.append(pipeline["name"])

    return {
        "kind": "pipeline",
        "name": "py-tests",
        "steps": [],
        "depends_on": depends_on,
    }


# Builds a single test pipeline
def test(docker_tag, python_cmd="python", tox_env="py3"):
    return {
        "kind": "pipeline",
        "name": "test-{}".format(docker_tag.replace(":", "")),
        "workspace": get_workspace(),
        "steps": [
            {
                "name": "test",
                "image": docker_tag,
                "environment": {
                    "TOXENV": tox_env,
                },
                "commands": [
                    "{} -V".format(python_cmd),
                    "pip install tox",
                    "tox",
                ],
            },
            notify_step()
        ]
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
    return {
        "kind": "pipeline",
        "name": "deploy-pypi",
        "trigger": {
            "event": ["tag"],
            "ref": [
                "refs/heads/master",
                "refs/tags/v*",
            ],
        },
        "depends_on": ["py-tests"],
        "workspace": get_workspace(),
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
    }


# Deploys image to docker hub
def push_docker(tag_suffix, arch, repo):
    return {
        "kind": "pipeline",
        "name": "deploy-docker-{}".format(tag_suffix),
        "trigger": {
            "event": ["tag"],
            "ref": [
                "refs/heads/master",
                "refs/tags/v*",
            ],
        },
        "workspace": get_workspace(),
        "steps": [
            {
                "name": "get qemu",
                "image": "busybox",
                "commands": ["sh ./get_qemu.sh {}".format(arch)],
            },
            {
                "name": "build",
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
            },
        ],
    }


# generate all docker pipelines to push images and manifest
def docker_pipelines():
    # build list of images to push
    docker_pipelines = [
        push_docker("linux-amd64", "x86_64", "library"),
        push_docker("linux-arm", "arm", "arm32v6"),
        push_docker("linux-arm64", "aarch64", "arm64v8"),
    ]

    # build list of dependencies
    pipeline_names = []
    for pipeline in docker_pipelines:
        pipeline_names.append(pipeline["name"])

    # append manifest pipeline
    docker_pipelines.append({
        "kind": "pipeline",
        "name": "deploy-docker-manifest",
        "trigger": {
            "event": ["tag"],
            "ref": [
                "refs/heads/master",
                "refs/tags/v*",
            ],
        },
        "workspace": get_workspace(),
        "depends_on": pipeline_names,
        "steps": [{
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
        }],
    })

    return docker_pipelines
