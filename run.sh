#!/usr/bin/env bash
# Run the Room Manager app.
# If a Python library is missing, ask to install it with pip and try again (until the app starts).
# Any other error is shown and the script stops.
#
# Usage:  ./run.sh        (or: bash run.sh)

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$ROOT/src/1.1 - sql-UI"   # the app loads its files with paths relative to this folder

# ---------------------------------------- find python ----------------------------------------
# the project virtual env first (Linux/macOS or Git Bash on Windows), then the system Python.
# every option is checked by really running it.
PYTHON=""
for CANDIDATE in "$ROOT/.venv/bin/python" "$ROOT/.venv/Scripts/python.exe" python3 python; do
    if "$CANDIDATE" --version >/dev/null 2>&1; then
        PYTHON="$CANDIDATE"
        break
    fi
done
if [ -z "$PYTHON" ]; then
    echo "ERROR: Python was not found. Install Python 3 and run this script again." >&2
    exit 1
fi

# pip package name for an import name, when they are not the same
pip_package_for() {
    case "$1" in
        psycopg2) echo "psycopg2-binary" ;;
        *) echo "$1" ;;
    esac
}

cd "$APP_DIR" || { echo "ERROR: can't find the app folder: $APP_DIR" >&2; exit 1; }
ERR_FILE="$(mktemp)"
trap 'rm -f "$ERR_FILE"' EXIT
INSTALLED=" "  # packages installed by this script, so we don't try the same one forever

while true; do
    echo "Starting Room Manager..."
    "$PYTHON" main.py 2> "$ERR_FILE"
    CODE=$?
    if [ "$CODE" -eq 0 ]; then
        exit 0  # the app was closed normally
    fi

    # "ModuleNotFoundError: No module named 'PyQt5.QtSvg'" -> PyQt5
    MODULE="$(sed -n "s/.*No module named '\([^']*\)'.*/\1/p" "$ERR_FILE" | tail -n 1)"
    MODULE="${MODULE%%.*}"

    # a missing file of the project itself is not a library -> it's a real error
    if [ -n "$MODULE" ] && { [ -e "$MODULE" ] || [ -e "$MODULE.py" ]; }; then
        MODULE=""
    fi

    if [ -z "$MODULE" ]; then
        echo
        echo "ERROR: the app stopped with an error (exit code $CODE):" >&2
        cat "$ERR_FILE" >&2
        exit "$CODE"
    fi

    PACKAGE="$(pip_package_for "$MODULE")"
    if [[ "$INSTALLED" == *" $PACKAGE "* ]]; then
        echo
        echo "ERROR: '$PACKAGE' was installed but Python still can't find the '$MODULE' library:" >&2
        cat "$ERR_FILE" >&2
        exit 1
    fi

    echo
    echo "The library '$MODULE' is missing."
    read -r -p "Install it now with: $PYTHON -m pip install $PACKAGE ? [y/N] " ANSWER
    case "$ANSWER" in
        [yY]|[yY][eE][sS]) ;;
        *) echo "Not installed - the app can't start without '$MODULE'."; exit 1 ;;
    esac

    if ! "$PYTHON" -m pip install "$PACKAGE"; then
        echo >&2
        echo "ERROR: installing '$PACKAGE' failed (see the pip message above)." >&2
        echo "If pip says the environment is 'externally managed', create a virtual env in the project folder:" >&2
        echo "    python3 -m venv \"$ROOT/.venv\"" >&2
        echo "and run this script again (it uses .venv automatically)." >&2
        exit 1
    fi
    INSTALLED="$INSTALLED$PACKAGE "
    echo
done
