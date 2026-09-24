import sqlite3
import psycopg2

OK_CODE = 111

MULTI_ORDERS=112

DELETE_CODE = 633

MAX_ORDERS_CODE = 996

UPDATE_ORDER_CODE = 112

ROOM_ERROR_CODE = 501

VERABLE_ERROR_CODE = 502

ERROR_CODE = 500

DB_CON = psycopg2.connect(host='localhost', dbname="hotel_manegmant", user='postgres', password="159633",
                          port=55555)
DB_CURSER = DB_CON.cursor()


stop_time_thread = False
CURRENT_USER = "TEST-USER"

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
