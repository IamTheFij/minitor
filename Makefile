env:
	virtualenv -p python3 env
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
	rm -fr ./build ./dist ./minitor.egg-info

.PHONY: install-hooks
install-hooks:
	tox -e pre-commit -- install -f --install-hooks
