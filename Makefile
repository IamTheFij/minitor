env:
	python3 -m venv env
	./env/bin/pip install -r requirements-dev.txt

.PHONY: run
run: env
	./env/bin/python -m minitor.main

.PHONY: test
test: env
	tox

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

.PHONY: dist-clean
dist-clean: clean
	rm -fr ./dist

.PHONY: install-hooks
install-hooks:
	tox -e pre-commit -- install -f --install-hooks

.coverage:
	tox

htmlcov/index.html: .coverage
	./env/bin/coverage html

.PHONY: open-coverage
open-coverage: htmlcov/index.html
	open htmlcov/index.html
