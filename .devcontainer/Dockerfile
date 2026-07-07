FROM mcr.microsoft.com/devcontainers/python:1-3.12

# Install uv from the official image (recommended by Astral)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install Task (https://taskfile.dev)
RUN curl -fsSL https://taskfile.dev/install.sh | sh -s -- -d -b /usr/local/bin

# The base image ships a Yarn apt source with an expired/missing GPG key, which breaks
# apt-get for any devcontainer feature (e.g. docker-in-docker). Remove it before apt installs.
# Use docker-ce-cli (not docker.io): the host daemon is bind-mounted and Docker 29+ requires API 1.44+.
# Install docker-compose-plugin so `docker compose` is available inside the devcontainer.
RUN rm -f /etc/apt/sources.list.d/yarn*.list 2>/dev/null || true \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli docker-compose-plugin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV UV_LINK_MODE=copy
