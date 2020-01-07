DOCKER_TAG := minitor-dev
OPEN_CMD := $(shell type xdg-open &> /dev/null && echo 'xdg-open' || echo 'open')
ENV := env

.PHONY: default
default: test

# Create sample config
config.yml:
	cp sample-config.yml config.yml

# Creates virtualenv
$(ENV):
	python3 -m venv $(ENV)

# Install minitor and dependencies in virtualenv
$(ENV)/bin/minitor: $(ENV)
	$(ENV)/bin/pip install -r requirements-dev.txt

# Install tox into virtualenv for running tests
$(ENV)/bin/tox: $(ENV)
	$(ENV)/bin/pip install tox

# Install wheel for building packages
$(ENV)/bin/wheel: $(ENV)
	$(ENV)/bin/pip install wheel

# Install twine for uploading packages
$(ENV)/bin/twine: $(ENV)
	$(ENV)/bin/pip install twine

# Installs dev requirements to virtualenv
.PHONY: devenv
devenv: $(ENV)/bin/minitor

# Generates a smaller env for running tox, which builds it's own env
.PHONY: test-env
test-env: $(ENV)/bin/tox

# Generates a small build env for building and uploading dists
.PHONY: build-env
build-env: $(ENV)/bin/twine $(ENV)/bin/wheel

# Runs Minitor
.PHONY: run
run: $(ENV)/bin/minitor config.yml
	$(ENV)/bin/minitor -vvv

# Runs Minitor with metrics
.PHONY: run-metrics
run-metrics: $(ENV)/bin/minitor config.yml
	$(ENV)/bin/minitor -vvv --metrics

# Runs tests with tox
.PHONY: test
test: $(ENV)/bin/tox
	$(ENV)/bin/tox -e py3

# Builds wheel for package to upload
.PHONY: build
build: $(ENV)/bin/wheel
	$(ENV)/bin/python setup.py sdist
	$(ENV)/bin/python setup.py bdist_wheel

# Verify that the python version matches the git tag so we don't push bad shas
.PHONY: verify-tag-version
verify-tag-version:
	$(eval TAG_NAME = $(shell [ -n "$(DRONE_TAG)" ] && echo $(DRONE_TAG) || git describe --tags --exact-match))
	test "v$(shell python setup.py -V)" = "$(TAG_NAME)"

# Uses twine to upload to pypi
.PHONY: upload
upload: verify-tag-version build $(ENV)/bin/twine
	$(ENV)/bin/twine upload dist/*

# Uses twine to upload to test pypi
.PHONY: upload-test
upload-test: verify-tag-version build $(ENV)/bin/twine
	$(ENV)/bin/twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# Cleans all build, runtime, and test artifacts
.PHONY: clean
clean:
	rm -fr ./build ./minitor.egg-info ./htmlcov ./.coverage ./.pytest_cache ./.tox
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete

# Cleans dist and env
.PHONY: dist-clean
dist-clean: clean
	rm -fr ./dist $(ENV)

# Install pre-commit hooks
.PHONY: install-hooks
install-hooks: $(ENV)
	$(ENV)/bin/tox -e pre-commit -- install -f --install-hooks

# Generates test coverage
.coverage:
	$(ENV)/bin/tox

# Builds coverage html
htmlcov/index.html: .coverage
	$(ENV)/bin/coverage html

# Opens coverage html in browser (on macOS and some Linux systems)
.PHONY: open-coverage
open-coverage: htmlcov/index.html
	$(OPEN_CMD) htmlcov/index.html

# Docker targets

# Targets to download required qemu binaries for running on an amd64 machine
build/qemu-x86_64-static:
	./get_qemu.sh x86_64

build/qemu-arm-static:
	./get_qemu.sh arm

build/qemu-aarch64-static:
	./get_qemu.sh aarch64

# Build Docker image for host architechture (amd64)
.PHONY: docker-build
docker-build: build/qemu-x86_64-static
	docker build . -t ${DOCKER_TAG}-linux-amd64

# Cross build for arm architechtures
.PHONY: docker-cross-build-arm
docker-cross-build-arm: build/qemu-arm-static
	docker build --build-arg REPO=arm32v6 --build-arg ARCH=arm . -t ${DOCKER_TAG}-linux-arm

.PHONY: docker-cross-build-arm64
docker-cross-build-arm64: build/qemu-aarch64-static
	docker build --build-arg REPO=arm64v8 --build-arg ARCH=aarch64 . -t ${DOCKER_TAG}-linux-arm64

# Run on host architechture
.PHONY: docker-run
docker-run: docker-build config.yml
	docker run --rm -v $(shell pwd)/config.yml:/app/config.yml ${DOCKER_TAG}-linux-amd64

# Cross run on host architechture
.PHONY: docker-cross-run-arm
docker-cross-run-arm: docker-cross-build-arm config.yml
	docker run --rm -v $(shell pwd)/config.yml:/app/config.yml ${DOCKER_TAG}-linux-arm

.PHONY: docker-cross-run-arm64
docker-cross-run-arm64: docker-cross-build-arm64 config.yml
	docker run --rm -v $(shell pwd)/config.yml:/app/config.yml ${DOCKER_TAG}-linux-arm64
