env:
	virtualenv -p python3 env
	./env/bin/pip install -r requirements.txt

run: env
	./env/bin/python -m minitor.main
