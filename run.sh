#!/usr/bin/env bash
# Run the Room Manager app (Linux / macOS / Git Bash on Windows).
# Finds Python and starts run_app.py, which asks to install missing libraries and shows any other error.
#
# Usage:  ./run.sh        (or: bash run.sh)

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# the project virtual env first, then the system Python. every option is checked by really running it.
for PYTHON in "$ROOT/.venv/bin/python" "$ROOT/.venv/Scripts/python.exe" python3 python; do
    if "$PYTHON" --version >/dev/null 2>&1; then
        exec "$PYTHON" "$ROOT/run_app.py" "$@"
    fi
done

echo "ERROR: Python was not found. Install Python 3 and run this script again." >&2
exit 1
