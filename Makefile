DOCKER_TAG := minitor-dev
OPEN_CMD := $(shell type xdg-open &> /dev/null && echo 'xdg-open' || echo 'open')

.PHONY: default
default: test

# Builds the python3 venv with all dev requirements
env:
	python3 -m venv env
	./env/bin/pip install -r requirements-dev.txt

# Runs Minitor
.PHONY: run
run: env
	./env/bin/python -m minitor.main -vvv

# Runs Minitor with metrics
.PHONY: run-metrics
run-metrics: env
	./env/bin/python -m minitor.main --metrics

# Generates a smaller env for running tox, which builds it's own env
.PHONY: test-env
test-env:
	python3 -m venv env
	./env/bin/pip install tox

# Runs tests with tox
.PHONY: test
test: env
	./env/bin/tox

# Generates a small build env for building and uploading dists
.PHONY: build-env
build-env:
	python3 -m venv env
	./env/bin/pip install twine wheel

# Builds wheel for package to upload
.PHONY: build
build: env
	./env/bin/python setup.py sdist
	./env/bin/python setup.py bdist_wheel

# Verify that the python version matches the git tag so we don't push bad shas
.PHONY: verify-tag-version
verify-tag-version:
	$(eval TAG_NAME = $(shell [ -n "$(DRONE_TAG)" ] && echo $(DRONE_TAG) || git describe --tags --exact-match))
	test "v$(shell python setup.py -V)" = "$(TAG_NAME)"

# Uses twine to upload to pypi
.PHONY: upload
upload: verify-tag-version build
	./env/bin/twine upload dist/*

# Uses twine to upload to test pypi
.PHONY: upload-test
upload-test: verify-tag-version build
	./env/bin/twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# Cleans all build, runtime, and test artifacts
.PHONY: clean
clean:
	rm -fr ./build ./minitor.egg-info ./htmlcov ./.coverage ./.pytest_cache ./.tox
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete

# Cleans dist and env
.PHONY: dist-clean
dist-clean: clean
	rm -fr ./dist ./env

# Install pre-commit hooks
.PHONY: install-hooks
install-hooks: env
	./env/bin/tox -e pre-commit -- install -f --install-hooks

# Generates test coverage
.coverage:
	./env/bin/tox

# Builds coverage html
htmlcov/index.html: .coverage
	./env/bin/coverage html

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

.PHONY: docker-cross-build-arm
docker-cross-build-arm64: build/qemu-aarch64-static
	docker build --build-arg REPO=arm64v8 --build-arg ARCH=aarch64 . -t ${DOCKER_TAG}-linux-arm64

# Run on host architechture
.PHONY: run
docker-run: docker-build
	docker run ${DOCKER_TAG}-linux-amd64

# Cross run on host architechture
.PHONY: docker-cross-run-arm
docker-cross-run-arm: docker-cross-build-arm
	docker run --rm ${DOCKER_TAG}-linux-arm

.PHONY: docker-cross-run-arm64
docker-cross-run-arm64: docker-cross-build-arm64
	docker run --rm ${DOCKER_TAG}-linux-arm64
