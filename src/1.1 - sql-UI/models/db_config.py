"""
Database connection settings.

Priority: environment variables > db_config.json (in the app folder, next to main.py) > built-in defaults.

db_config.json is NOT committed to git (see .gitignore) - copy db_config.example.json to db_config.json
next to it and edit it with your own database credentials. Without either, the app falls back to the
same local defaults it always used, so a fresh checkout still runs against a local dev database.
"""
import json
import os

_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # models/ is directly inside the app folder
_CONFIG_FILE = os.path.join(_APP_DIR, "db_config.json")

_DEFAULTS = {
    "host": "localhost",
    "port": 55555,
    "dbname": "hotel_manegmant",
    "user": "postgres",
    "password": "159633",
}


def _from_file():
    if not os.path.isfile(_CONFIG_FILE):
        return {}
    with open(_CONFIG_FILE) as f:
        return json.load(f)


def get():
    """The connection settings to use, as a dict with host/port/dbname/user/password"""
    config = dict(_DEFAULTS)
    config.update(_from_file())
    for key in list(config):
        env_value = os.environ.get(f"ROOM_MANAGER_DB_{key.upper()}")
        if env_value is not None:
            config[key] = int(env_value) if key == "port" else env_value
    return config
