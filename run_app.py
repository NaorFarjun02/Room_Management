"""
Start the Room Manager app.

If the app stops because a Python library is missing, ask whether to install it with pip and run the app
again - repeating until it starts. Any other error is shown and the launcher stops.

Normally started by run.sh / run.cmd, but it can also be run directly:  python run_app.py
Only the Python standard library is used, so it works before anything is installed.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(ROOT, "src", "1.1 - sql-UI")  # the app loads its files with paths relative to this folder

PIP_NAMES = {"psycopg2": "psycopg2-binary"}  # pip package name for an import name, when they are not the same
MISSING_MODULE = re.compile(r"No module named '([^']+)'")


def missing_library(error_text, app_dir=APP_DIR):
    """
    The library that is missing according to the app's error output, or None.
    "No module named 'PyQt5.QtSvg'" -> "PyQt5". A missing module of the project itself (like "models")
    is not a library that pip can install, so it is None too.
    """
    found = MISSING_MODULE.findall(error_text)
    if not found:
        return None
    module = found[-1].split(".")[0]
    if os.path.exists(os.path.join(app_dir, module)) or os.path.exists(os.path.join(app_dir, module + ".py")):
        return None
    return module


def pip_package(module):
    return PIP_NAMES.get(module, module)


def ask_yes_no(question, input_func=input):
    """y / Y / yes -> True. Anything else, or no input at all (EOF), -> False"""
    try:
        answer = input_func(question)
    except EOFError:
        return False
    return answer.strip().lower() in ("y", "yes")


def run_app(python=sys.executable, app_dir=APP_DIR):
    """Run the app and wait until it is closed. Returns (exit code, what the app wrote to stderr)"""
    result = subprocess.run([python, "main.py"], cwd=app_dir, stderr=subprocess.PIPE,
                            universal_newlines=True, errors="replace")
    return result.returncode, result.stderr


def pip_install(package, python=sys.executable):
    """Install the package with pip, return True if it worked"""
    return subprocess.call([python, "-m", "pip", "install", package]) == 0


def main(runner=run_app, installer=pip_install, ask=ask_yes_no, app_dir=APP_DIR, out=sys.stdout, err=sys.stderr):
    """The launcher loop, returns the exit code for the script (0 = the app ran and was closed normally)"""
    if not os.path.isfile(os.path.join(app_dir, "main.py")):
        print(f"ERROR: can't find the app: {os.path.join(app_dir, 'main.py')}", file=err)
        return 1
    installed = set()  # packages installed by the launcher, so we don't try the same one forever

    while True:
        print("Starting Room Manager...", file=out, flush=True)
        code, error_text = runner()
        if code == 0:
            return 0  # the app was closed normally

        module = missing_library(error_text, app_dir)
        if module is None:
            print(f"\nERROR: the app stopped with an error (exit code {code}):", file=err)
            print(error_text.rstrip(), file=err)
            return code if isinstance(code, int) and 0 < code < 256 else 1

        package = pip_package(module)
        if package in installed:
            print(f"\nERROR: '{package}' was installed but Python still can't find the '{module}' library:", file=err)
            print(error_text.rstrip(), file=err)
            return 1

        print(f"\nThe library '{module}' is missing.", file=out, flush=True)
        if not ask(f"Install it now with: pip install {package} ? [y/N] "):
            print(f"Not installed - the app can't start without '{module}'.", file=out)
            return 1

        if not installer(package):
            print(f"\nERROR: installing '{package}' failed (see the pip message above).", file=err)
            print("If pip says the environment is 'externally managed', create a virtual env in the project folder:",
                  file=err)
            print(f"    python3 -m venv \"{os.path.join(ROOT, '.venv')}\"", file=err)
            print("and run the script again (run.sh / run.cmd use .venv automatically).", file=err)
            return 1
        installed.add(package)
        print(file=out)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(130)
