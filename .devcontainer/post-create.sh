#!/usr/bin/env bash
set -euo pipefail

# Allow the vscode user to talk to the host Docker daemon (socket is bind-mounted).
if [ -S /var/run/docker.sock ]; then
    DOCKER_GID="$(stat -c '%g' /var/run/docker.sock)"
    if ! getent group docker >/dev/null; then
        sudo groupadd --gid "${DOCKER_GID}" docker
    fi
    sudo usermod -aG docker vscode
fi

uv sync --all-groups
uv run playwright install chromium --with-deps
