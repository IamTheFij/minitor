ARG REPO=library
FROM ${REPO}/python:3-alpine
LABEL maintainer="ian@iamthefij.com"
# Minitor: https://git.iamthefij.com/iamthefij/minitor

# This should be the target qemu arch
ARG ARCH=x86_64
COPY ./build/qemu-${ARCH}-static /usr/bin/

# Add common checking tools
RUN apk --no-cache add bash=~5.1 curl=~7.80 jq=~1.6
WORKDIR /app

# Add minitor user for running as non-root
RUN addgroup -S minitor && adduser -S minitor -G minitor

# Expose default metrics port
EXPOSE 8080

# Copy default sample config
COPY ./sample-config.yml /app/config.yml

# Copy Python package to container
COPY ./README.md /app/
COPY ./setup.py /app/
COPY ./minitor /app/minitor
RUN pip install --no-cache-dir -e .

# Copy scripts
COPY ./scripts /app/scripts

# Allow all users to execute minitor and scripts
RUN chmod -R 755 /app

# Drop to non-root user
USER minitor

ENTRYPOINT [ "python3", "-m", "minitor.main" ]
