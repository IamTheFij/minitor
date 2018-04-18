FROM python:3

COPY ./sample-config.yml /app/config.yml
WORKDIR /app

COPY ./README.md /app/
COPY ./setup.py /app/
COPY ./minitor /app/minitor
RUN pip install -e .

ENTRYPOINT python -m minitor.main
