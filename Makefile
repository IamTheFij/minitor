env:
	virtualenv -p python3 env
	./env/bin/pip install -r requirements.txt

.PHONY: run
run: env
	./env/bin/python -m minitor.main

.PHONY: build
build: env
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
