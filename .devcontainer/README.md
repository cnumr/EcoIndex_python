# Dev Container — EcoIndex Python

## Prerequisites (machine running Docker)

- [Docker](https://docs.docker.com/get-docker/) (daemon running)
- Cursor with the **Dev Containers** extension (Anysphere)

Nothing to install on a Windows PC for **uv**: everything is in the image / `post-create`.

## Cursor error: `path must be of type string. Received undefined`

Known Cursor bug with **Remote SSH → Dev Container** (the Docker build succeeds; the failure happens when installing the Cursor server inside the container).

Reference: [Cursor forum](https://forum.cursor.com/t/failed-to-install-cursor-server-the-path-argument-must-be-of-type-string-received-undefined/155076)

### Recommended workaround

On the remote machine (where the repo lives, e.g. over SSH):

```bash
cd /path/to/EcoIndex_python
./.devcontainer/up.sh
```

Then in Cursor:

1. **Command Palette** → `Dev Containers: Attach to Running Container` → container **`ecoindex-python-dev`**
2. **File → Open Folder…** → `/workspaces/<project-folder-name>` (e.g. `/workspaces/EcoIndex_python` — the `up.sh` script prints the exact path)

Without step 2, the explorer stays empty: **Attach** does not open the project folder automatically (SSH workaround).

Alternative: `Dev Containers: Open Folder in Container…` (same path).

Avoid for now: **Reopen in Container** / **Rebuild and Reopen in Container** (often triggers the bug).

### Checks on the SSH host

```bash
echo "$HOME"          # must not be empty
test -f ~/.gitconfig && echo "gitconfig OK"
```

If `$HOME` is empty, add to `~/.bashrc` or `~/.zshrc`:

```bash
export HOME=/home/your_username
```

### Cursor extensions

- Keep **Dev Containers** (Anysphere)
- Disable **Dev Containers** (Microsoft) if both are installed (possible conflicts)
