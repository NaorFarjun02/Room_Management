import functools
import sqlite3
import sys

import psycopg2

from . import db_config

OK_CODE = 111

MULTI_ORDERS=112

DELETE_CODE = 633

MAX_ORDERS_CODE = 996

UPDATE_ORDER_CODE = 112

ROOM_ERROR_CODE = 501

VERABLE_ERROR_CODE = 502

ERROR_CODE = 500

_db_settings = db_config.get()
try:
    DB_CON = psycopg2.connect(host=_db_settings["host"], dbname=_db_settings["dbname"], user=_db_settings["user"],
                              password=_db_settings["password"], port=_db_settings["port"])
except psycopg2.OperationalError as e:
    sys.exit(f"Can't connect to the database: {e}\n"
             f"Copy db_config.example.json to db_config.json (next to main.py) and set your database settings there, "
             f"or set the ROOM_MANAGER_DB_* environment variables.")
DB_CURSER = DB_CON.cursor()


def rollback_on_error(func):
    """Decorator for a database function: if it raises, roll back the open transaction before re-raising.
    Without this, one failed query leaves the connection in an aborted state and every query after it fails."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            DB_CON.rollback()
            raise
    return wrapper


windows_indexes = {

    "home-menu": 0,

    "new-order": 1,

    "rooms-view": 2,

    "view-order": 3,

    "update-order": 4,

    "settings": 5,

    "orders": 6,

    "manager-page": 7,

    "login-create": 8,

    "msg-box": 33,

}  # A list of all the indexes of each page

# def create_msg_dialog(msg,btn1_text,btn2_text):
# 	dialog = MSG_Dialog("go to rooms", "bobo1", "gogo2")
# 	dialog.exec_()
# 	status = dialog.status
# 	return status
