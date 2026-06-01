#!/usr/bin/env bash
# Start the dev container without relying on Cursor's "Reopen in Container" (SSH workaround).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
echo "Starting dev container for ${ROOT} ..."
npx --yes @devcontainers/cli@latest up \
  --workspace-folder "${ROOT}" \
  --remove-existing-container
echo ""
WORKSPACE_IN_CONTAINER="/workspaces/$(basename "${ROOT}")"
echo "Container started. Workspace is mounted at: ${WORKSPACE_IN_CONTAINER}"
echo ""
echo "In Cursor:"
echo "  1. Dev Containers → Attach to Running Container → ecoindex-python-dev"
echo "  2. File → Open Folder… → ${WORKSPACE_IN_CONTAINER}"
echo ""
echo "Or use: Dev Containers → Open Folder in Container… (same path)"
