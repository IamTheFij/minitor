FROM python:3

RUN pip install --no-cache-dir minitor
WORKDIR /app
COPY config.yml /app/config.yml
CMD minitor