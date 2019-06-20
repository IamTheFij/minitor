ARG REPO=library
FROM ${REPO}/python:3-alpine
LABEL maintainer="ian@iamthefij.com"
# Minitor: https://git.iamthefij.com/iamthefij/minitor

# This should be the target qemu arch
ARG ARCH=x86_64
COPY ./build/qemu-${ARCH}-static /usr/bin/

COPY ./sample-config.yml /app/config.yml
WORKDIR /app

# Expose default metrics port
EXPOSE 8080

# Copy Python package to container
COPY ./README.md /app/
COPY ./setup.py /app/
COPY ./minitor /app/minitor
RUN pip install -e .

# Copy scripts
COPY ./scripts /app/scripts

ENTRYPOINT [ "python3", "-m", "minitor.main" ]
