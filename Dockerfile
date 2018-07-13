FROM python:3
LABEL maintainer="ian@iamthefij.com"
# Minitor: https://git.iamthefij.com/iamthefij/minitor

COPY ./sample-config.yml /app/config.yml
WORKDIR /app

# Expose default metrics port
EXPOSE 8080

COPY ./README.md /app/
COPY ./setup.py /app/
COPY ./minitor /app/minitor
RUN pip install -e .

ENTRYPOINT [ "python3", "-m", "minitor.main" ]
