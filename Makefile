env:
	python3 -m venv env
	./env/bin/pip install -r requirements-dev.txt

.PHONY: run
run: env
	./env/bin/python -m minitor.main

.PHONY: test
test: env
	./env/bin/tox

.PHONY: build
build: test
	./env/bin/python setup.py sdist
	./env/bin/python setup.py bdist_wheel

.PHONY: upload
upload: env
	./env/bin/twine upload dist/*

.PHONY: upload-test
upload-test: env
	./env/bin/twine upload --repository-url https://test.pypi.org/legacy/ dist/*

.PHONY: clean
clean:
	rm -fr ./build ./minitor.egg-info ./htmlcov ./.coverage ./.pytest_cache ./.tox
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete

.PHONY: dist-clean
dist-clean: clean
	rm -fr ./dist ./env

.PHONY: install-hooks
install-hooks:
	./env/bin/tox -e pre-commit -- install -f --install-hooks

.coverage:
	./env/bin/tox

htmlcov/index.html: .coverage
	./env/bin/coverage html

.PHONY: open-coverage
open-coverage: htmlcov/index.html
	open htmlcov/index.html
