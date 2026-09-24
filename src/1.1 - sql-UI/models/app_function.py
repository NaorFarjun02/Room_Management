import random

from datetime import datetime, date, timedelta

from .Logs import *
from .global_ver import *
from .range_of_dates import Dates_Range
from . import auth
from . import session
from . import activity_log

#################################### Setup Database ####################################
def create_DB():
    # DB_CURSER.execute("DROP TABLE IF EXISTS rooms")
    # DB_CURSER.execute("DROP TABLE IF EXISTS rooms_faults")
    # DB_CURSER.execute("DROP TABLE IF EXISTS dates_range")
    # DB_CURSER.execute("DROP TABLE IF EXISTS orders")

    DB_CURSER.execute(
        """CREATE TABLE IF NOT EXISTS rooms(room_number INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        room_capacity INTEGER not null,
        room_is_catch bool DEFAULT false  check(room_is_catch in (false,true)),
        room_is_clean bool DEFAULT false  check(room_is_clean in (false,true)))"""
    )
    DB_CURSER.execute("ALTER TABLE rooms ADD COLUMN IF NOT EXISTS room_name TEXT")  # optional display name
    DB_CURSER.execute("""CREATE UNIQUE INDEX IF NOT EXISTS rooms_room_name_lower_idx
        ON rooms (lower(room_name)) WHERE room_name IS NOT NULL""")
    DB_CURSER.execute(
        """CREATE TABLE IF NOT EXISTS  rooms_faults(room_number INTEGER,
        fault text not null)"""
    )
    DB_CURSER.execute(
        """CREATE TABLE IF NOT EXISTS  dates_range(order_id INTEGER PRIMARY KEY,
        room_number INTEGER,
        start_date text not null,
        end_date text not null)"""
    )
    DB_CURSER.execute(
        """CREATE TABLE IF NOT EXISTS orders(id SERIAL  PRIMARY KEY,
        customer_name text not null,
        number_of_guests integer not null,
        room_number integer not null,
        breakfast bool check(breakfast in (false,true)),
        lunch bool check(lunch in (false,true)),
        dinner bool check(dinner in (false,true)),
        electric_car bool check(electric_car in (false,true)),
        pet bool check(pet in (false,true)),
        check_in bool DEFAULT false check(check_in in (false,true)),
        check_out bool DEFAULT false check(check_out in (false,true)),
        create_time text not null,
        create_by text not null)"""
    )
    DB_CURSER.execute(
        """CREATE TABLE IF NOT EXISTS users(id SERIAL PRIMARY KEY,
        username text not null,
        full_name text not null,
        role text not null check(role in ('manager','desk')),
        password_hash text not null,
        is_active bool not null default true,
        created_at timestamp not null default now(),
        last_login timestamp)"""
    )
    DB_CURSER.execute("""CREATE UNIQUE INDEX IF NOT EXISTS users_username_lower_idx ON users (lower(username))""")
    DB_CURSER.execute(
        """CREATE TABLE IF NOT EXISTS activity_log(id SERIAL PRIMARY KEY,
        created_at timestamp not null default now(),
        category text not null,
        actor text,
        summary text not null)"""
    )
    DB_CURSER.execute("""CREATE INDEX IF NOT EXISTS activity_log_created_at_idx ON activity_log (created_at DESC)""")
    DB_CON.commit()

#################################### Get data from DB ####################################
def get_order_from_db_by_id(order_id: int = -1):
    if order_id == -1:
        return ERROR_CODE, "ORDER_ID can't be -1"
    DB_CURSER.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order = DB_CURSER.fetchone()
    if order == None:
        return [ERROR_CODE, f"ORDER_ID --{order_id}-- not exsist"]
    return [OK_CODE,order]

def get_order_from_db_by_customer_name(customer_name: str = ""):
    if customer_name == "":
        return ERROR_CODE, "customer_name can't be empty"
    get_q = ("""SELECT * FROM orders WHERE customer_name = %s """)
    DB_CURSER.execute(get_q, (customer_name,))
    order = DB_CURSER.fetchall()
    if order == []:
        return [ERROR_CODE, f"CUSTOMER_NAME {customer_name} not exsist"]
    if len(order) > 1:
        return [MULTI_ORDERS,order]
    return [OK_CODE,order]

def get_room_from_db(room_number: int = -1):
    if room_number == -1:
        return ERROR_CODE, "ROOM_NUMBER can't be -1"
    DB_CURSER.execute("SELECT * FROM rooms WHERE room_number = %s", (room_number,))
    room = DB_CURSER.fetchone()
    if room == None:
        return [ERROR_CODE, f"room --{room_number}-- dosn't exsist"]
    return room

def get_check_in_and_out_status(order_id=-1):
    DB_CURSER.execute("select check_in,check_out from orders where id = %s", (order_id,))
    order_check_in_status, order_check_out_status = DB_CURSER.fetchone()
    return order_check_in_status, order_check_out_status

def get_start_and_end_dates(order_id=-1):
    DB_CURSER.execute("select start_date,end_date from dates_range where order_id = %s", (order_id,))
    start_date, end_date = DB_CURSER.fetchone()
    return start_date, end_date

def get_active_order_in_room_db(order_id):
    """
    Another order in the same room as this order that is checked-in and not checked-out
    (id, customer_name, room_number, end_date) or None
    """
    DB_CURSER.execute("""
        SELECT o.id, o.customer_name, o.room_number, d.end_date
        FROM orders o LEFT JOIN dates_range d ON d.order_id = o.id
        WHERE o.room_number = (SELECT room_number FROM orders WHERE id = %s)
            AND o.id <> %s AND o.check_in AND NOT o.check_out
        ORDER BY o.id LIMIT 1""", (order_id, order_id))
    return DB_CURSER.fetchone()

def is_order_overdue(end_date, check_in, check_out):
    """True if the guest is checked-in, not checked-out and the leaving date (dd/mm/yyyy) already passed"""
    if not end_date or not check_in or check_out:
        return False
    return datetime.strptime(end_date, "%d/%m/%Y").date() < date.today()

def get_date_range_by_room_id_db(room_number=-1):
    DB_CURSER.execute("select start_date,end_date from dates_range where room_number = %s", (room_number,))
    dates_for_room = DB_CURSER.fetchall()
    return dates_for_room

def room_display_name(room_number, room_name=None):
    """"Room 4", or the room's own name when it has one"""
    return room_name if room_name else f"Room {room_number}"

#################################### Insert data to DB ####################################
def create_date_range_in_db(order_id, room_number, date_range):
    """create a date range in the date_range table for the room and order"""
    DB_CURSER.execute("select * from dates_range where order_id = %s", (order_id,))
    check_date_range_for_order = DB_CURSER.fetchone()
    if check_date_range_for_order != None:
        return [ERROR_CODE, f"date_range from order:{order_id} exsis --> {check_date_range_for_order}"]
    date_range_to_db = [
        order_id,
        room_number,
        date_range.get_arrival_date(),
        date_range.get_leaving_date(),
    ]
    DB_CURSER.execute("INSERT INTO dates_range VALUES(%s,%s,%s,%s)", date_range_to_db)
    return OK_CODE, f"Date range for order {order_id} created: {date_range.get_arrival_date()} - {date_range.get_leaving_date()}"

def create_order_in_db(order_info):
    DB_CURSER.execute(
        """INSERT INTO orders (customer_name,number_of_guests,room_number, breakfast ,lunch ,dinner ,electric_car ,pet ,create_time ,create_by )
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id""",
        order_info,
    )
    return DB_CURSER.fetchone()[0]

#################################### Side functions ####################################

def get_one_data_from_db(sql="", params=[]):
    DB_CURSER.execute(sql, params)
    return DB_CURSER.fetchone()

def get_multi_data_from_db(sql="", params=[]):
    DB_CURSER.execute(sql, params)
    return DB_CURSER.fetchall()

#################################### Menu options ####################################

# ====================================================section 11 - add new room fault====================================================
@rollback_on_error
def add_new_room_fault(room_number, fault):
    DB_CURSER.execute("INSERT INTO rooms_faults VALUES(%s,%s)", [room_number, fault])
    activity_log.log_activity("fault_added", f"Room {room_number}: {fault}", actor=session.current.username)
    DB_CON.commit()

@rollback_on_error
def delete_room_fault_db(room_number, fault):
    """Remove one fault from the room (the fault was fixed)"""
    DB_CURSER.execute("""
        DELETE FROM rooms_faults WHERE ctid IN (
            SELECT ctid FROM rooms_faults WHERE room_number = %s AND fault = %s LIMIT 1)""", (room_number, fault))
    activity_log.log_activity("fault_resolved", f"Room {room_number}: {fault}", actor=session.current.username)
    DB_CON.commit()
    return OK_CODE, f"Fault fixed in room {room_number}"

# ========================================================================================================================================
# --------------------------------------------------------------------------------------------------------------------------------------------
# ====================================================section 10 - delete order====================================================
def delete_date_range_from_db_by_order(order_id: int = -1):
    if order_id == -1:
        return ERROR_CODE, "ORDER_ID can't be -1"
    DB_CURSER.execute("DELETE FROM dates_range WHERE order_id = %s", (order_id,))

@auth.require_permission("delete_order")
@rollback_on_error
def delete_order_from_db_by_id(delete_code: int = 0, order_id: int = -1):
    # try:
    if delete_code != DELETE_CODE:  # Must have a delete code to confirm the delete
        return ERROR_CODE, f"Error -> Delete code not mach : {delete_code}"
    if order_id == -1:
        return ERROR_CODE, "ORDER_ID can't be -1"
    order = get_order_from_db_by_id(order_id)  # Search the order
    delete_date_range_from_db_by_order(order_id=order_id)
    DB_CURSER.execute("DELETE FROM orders WHERE id = %s", (order_id,))

    # move_order_to_history(order)  # Add the order to history
    customer_name = order[1][1] if order[0] == OK_CODE else "?"
    activity_log.log_activity("order_deleted", f"Order #{str(order_id).zfill(8)} ({customer_name}) deleted",
                              actor=session.current.username)
    DB_CON.commit()
    return OK_CODE, f"Order number {order_id} deleted"
    # except Exception as e:
    #     return ERROR_CODE, f"Error -> {e}"

# ==================================================================================================================================
# --------------------------------------------------------------------------------------------------------------------------------------------
# ====================================================section 9 - LOGS====================================================
# =========================================================================================================================
# --------------------------------------------------------------------------------------------------------------------------------------------
# ====================================================section 7 - check-out====================================================

def check_out_db(order_id=-1):
    try:
        in_status, out_status = get_check_in_and_out_status(order_id)
        if in_status and not out_status:
            today = date.today()
            start_date, end_date = get_start_and_end_dates(order_id)
            arrival = datetime.strptime(start_date, "%d/%m/%Y").date()
            if today < arrival:
                # check-out is possible from the arrival day (leaving early / late is ok)
                return False, (f"Check-out is only possible from the arrival day ({start_date}). "
                               f"Today is {today.strftime('%d/%m/%Y')}.")
            DB_CURSER.execute("update orders set check_out = TRUE where id = %s", (order_id,))
            # the guest left -> the room needs cleaning
            DB_CURSER.execute("""UPDATE rooms SET room_is_clean = FALSE
                WHERE room_number = (SELECT room_number FROM orders WHERE id = %s)""", (order_id,))
            activity_log.log_activity("check_out", f"Order #{str(order_id).zfill(8)} checked out",
                                      actor=session.current.username)
            DB_CON.commit()
            return True, ""
        elif out_status:
            return False, "The customer is already check out!!"
        elif not in_status:
            return False, "The customer not check-in yet!!"
    except Exception as e:
        DB_CON.rollback()
        print("check-out in db: ", e)
        return False, f"Can't check-out: {e}"

@rollback_on_error
def cancel_check_out_db(order_id=-1):
    in_status, out_status = get_check_in_and_out_status(order_id)
    if in_status and out_status:
        DB_CURSER.execute("update orders set check_out = FALSE where id = %s", (order_id,))
        activity_log.log_activity("check_out_cancelled", f"Order #{str(order_id).zfill(8)} check-out cancelled",
                                  actor=session.current.username)
        DB_CON.commit()
        return OK_CODE, ""
    else:
        return ERROR_CODE, "Can't cancel the check-out if the user is not check-out"

# ==============================================================================================================================
# --------------------------------------------------------------------------------------------------------------------------------------------
# ====================================================section 6 - check-in=====================================================


def check_in_db(order_id=-1):
    try:
        in_status, out_status = get_check_in_and_out_status(order_id)
        if not in_status and not out_status:
            today = date.today()
            start_date, end_date = get_start_and_end_dates(order_id)
            arrival = datetime.strptime(start_date, "%d/%m/%Y").date()
            leaving = datetime.strptime(end_date, "%d/%m/%Y").date()
            if not (arrival <= today < leaving):
                # check-in is possible from the arrival day until the day before leaving
                last_day = (leaving - timedelta(days=1)).strftime("%d/%m/%Y")
                return False, (f"Check-in is only possible from {start_date} until {last_day} (the day before leaving). "
                               f"Today is {today.strftime('%d/%m/%Y')}.")
            active_order = get_active_order_in_room_db(order_id)
            if active_order is not None:
                # another guest is still checked-in in the room -> can't check-in, return the order so the user can go to it
                active_id, active_customer, active_room, active_end = active_order
                msg = f"Room {active_room} still has an open order: #{str(active_id).zfill(8)} ({active_customer})."
                if active_end and datetime.strptime(active_end, "%d/%m/%Y").date() < today:
                    msg += f" Its leaving date {active_end} has passed and it was not checked-out."
                return False, msg + " Check-out that order first.", active_id
            DB_CURSER.execute("update orders set check_in = TRUE where id = %s", (order_id,))
            activity_log.log_activity("check_in", f"Order #{str(order_id).zfill(8)} checked in",
                                      actor=session.current.username)
            DB_CON.commit()
            return True, ""
        elif in_status:
            return False, "The customer is already check in!!"
        elif out_status:
            return False, "The customer is already check out!!"
    except Exception as e:
        DB_CON.rollback()
        print("check-in in db: ", e)
        return False, f"Can't check-in: {e}"

@rollback_on_error
def cancel_check_in_db(order_id=-1):
    in_status, out_status = get_check_in_and_out_status(order_id)
    if in_status and not out_status:
        DB_CURSER.execute("update orders set check_in = FALSE where id = %s", (order_id,))
        activity_log.log_activity("check_in_cancelled", f"Order #{str(order_id).zfill(8)} check-in cancelled",
                                  actor=session.current.username)
        DB_CON.commit()
        return OK_CODE, ""
    else:
        return ERROR_CODE, "Can't cancel the check-in if the user is already check-out"

# =============================================================================================================================
# --------------------------------------------------------------------------------------------------------------------------------------------
# ====================================================section 5 - get rooms====================================================
def get_room_faults_from_db(room_number):
    DB_CURSER.execute("SELECT fault FROM rooms_faults WHERE room_number = %s", (room_number,))
    rooms_list = DB_CURSER.fetchall()
    return rooms_list

def get_rooms_from_db():
    DB_CURSER.execute("SELECT * FROM rooms")
    rooms_list = DB_CURSER.fetchall()
    return rooms_list

@rollback_on_error
def get_rooms_status_from_db():
    """
    All the rooms with their live status:
    (room_number, room_capacity, occupied_now, room_is_clean, faults_count, overdue_order_id, room_name)
    occupied_now = the room is marked as catch OR a guest is checked-in (and not checked-out) in it
    overdue_order_id = an order in the room that its leaving date passed but it was not checked-out (None if there isn't)
    """
    DB_CURSER.execute("""
        SELECT r.room_number, r.room_capacity,
            (r.room_is_catch OR EXISTS(SELECT 1 FROM orders o
                                       WHERE o.room_number = r.room_number AND o.check_in AND NOT o.check_out)),
            r.room_is_clean,
            (SELECT COUNT(*) FROM rooms_faults rf WHERE rf.room_number = r.room_number),
            (SELECT o.id FROM orders o JOIN dates_range d ON d.order_id = o.id
             WHERE o.room_number = r.room_number AND o.check_in AND NOT o.check_out
                AND to_date(d.end_date, 'DD/MM/YYYY') < CURRENT_DATE
             ORDER BY o.id LIMIT 1),
            r.room_name
        FROM rooms r
        ORDER BY r.room_number""")
    return DB_CURSER.fetchall()

@rollback_on_error
def get_all_orders_from_db(include_closed=False):
    """
    All the orders with their dates, open orders only by default (closed = the customer checked-out)
    (id, customer_name, number_of_guests, room_number, check_in, check_out, start_date, end_date, room_name)
    """
    sql = """
        SELECT o.id, o.customer_name, o.number_of_guests, o.room_number, o.check_in, o.check_out,
            d.start_date, d.end_date, r.room_name
        FROM orders o
        LEFT JOIN dates_range d ON d.order_id = o.id
        LEFT JOIN rooms r ON r.room_number = o.room_number
        """
    if not include_closed:
        sql += " WHERE o.check_out = FALSE "
    sql += " ORDER BY to_date(d.start_date, 'DD/MM/YYYY') NULLS LAST, o.id"
    DB_CURSER.execute(sql)
    return DB_CURSER.fetchall()

# =============================================================================================================================
# --------------------------------------------------------------------------------------------------------------------------------------------
# ====================================================section 4 - delete room====================================================
@auth.require_permission("delete_room")
def delete_room_db(room_number=-1):
    if room_number == -1:
        return ERROR_CODE, "Room dose not exist"
    try:
        DB_CURSER.execute("DELETE FROM rooms WHERE room_number = %s", (room_number,))
        activity_log.log_activity("room_deleted", f"Room {room_number} deleted", actor=session.current.username)
        DB_CON.commit()
        return OK_CODE, f"Room {room_number} deleted"

    except Exception as e:
        DB_CON.rollback()
        return ERROR_CODE, f"Can't delete room: {e}"

# ==============================================================================================================================
# --------------------------------------------------------------------------------------------------------------------------------------------
# ====================================================section 3 - add new room====================================================
@auth.require_permission("add_room")
@rollback_on_error
def create_room_in_db(room_capacity: int):
    DB_CURSER.execute("INSERT INTO rooms (room_capacity) VALUES(%s) RETURNING room_number", (room_capacity,))
    room_number = DB_CURSER.fetchone()[0]
    activity_log.log_activity("room_created", f"Room {room_number} created (capacity {room_capacity})",
                              actor=session.current.username)
    DB_CON.commit()
    return OK_CODE, "Room created"

@rollback_on_error
def set_room_clean_db(room_number, clean=True):
    """Mark the room as clean (or as needs cleaning when clean=False)"""
    DB_CURSER.execute("UPDATE rooms SET room_is_clean = %s WHERE room_number = %s", (clean, room_number))
    if clean:  # only log the deliberate "Mark clean" action, not the automatic dirty-on-checkout side effect
        activity_log.log_activity("room_marked_clean", f"Room {room_number} marked clean", actor=session.current.username)
    DB_CON.commit()
    return OK_CODE, f"Room {room_number} is {'clean' if clean else 'needs cleaning'}"

@auth.require_permission("rename_room")
@rollback_on_error
def set_room_name_db(room_number, name):
    """Set (or, with an empty name, clear) the room's display name. Names must be unique."""
    name = (name or "").strip() or None
    if name and len(name) > 30:
        return ERROR_CODE, "Room name can be at most 30 characters"
    if name:
        DB_CURSER.execute("SELECT room_number FROM rooms WHERE lower(room_name) = lower(%s) AND room_number <> %s",
                          (name, room_number))
        if DB_CURSER.fetchone():
            return ERROR_CODE, f"Room name '{name}' is already used by another room"
    DB_CURSER.execute("UPDATE rooms SET room_name = %s WHERE room_number = %s", (name, room_number))
    summary = f"Room {room_number} renamed to '{name}'" if name else f"Room {room_number}'s name was cleared"
    activity_log.log_activity("room_renamed", summary, actor=session.current.username)
    DB_CON.commit()
    return OK_CODE, "Room name updated"

# =================================================================================================================================
# --------------------------------------------------------------------------------------------------------------------------------------------
# ====================================================section 2 - update order====================================================

@rollback_on_error
def update_order_db(order_id: int = -1, customer_name: str = "", number_of_guests: int = 0,
                    breakfast: bool = False, lunch: bool = False, dinner: bool = False,
                    electric_car: bool = False, pet: bool = False, arrival_date: str = "", leaving_date: str = ""):
    order_status = get_order_from_db_by_id(order_id)
    if order_status[0] != OK_CODE:
        return ERROR_CODE, order_status[1]
    order = order_status[1]  # id, customer_name, number_of_guests, room_number, ..., pet, check_in, check_out, ...
    exist_guests, room_number, checked_in, checked_out = order[2], order[3], order[9], order[10]
    exist_arrival_date, exist_leaving_date = get_start_and_end_dates(order_id)
    if customer_name == "":
        customer_name = order[1]
    if number_of_guests == 0:
        number_of_guests = exist_guests
    if number_of_guests < 1:
        return VERABLE_ERROR_CODE, "The order must have at least 1 guest"
    if arrival_date == "" or leaving_date == "":
        arrival_date, leaving_date = exist_arrival_date, exist_leaving_date
    if exist_guests != number_of_guests or exist_arrival_date != arrival_date or exist_leaving_date != leaving_date:
        new_date_range = Dates_Range(arrival_date, leaving_date)
        if not new_date_range.range_ok:
            return VERABLE_ERROR_CODE, new_date_range.error_text
        delete_date_range_from_db_by_order(order_id)  # free the old dates, so they don't block the search below
        if not is_room_available(room_number, number_of_guests, new_date_range):  # keep the same room when it's free
            if checked_in and not checked_out:
                # the guest is already in the room -> don't move them to another room behind their back
                DB_CON.rollback()
                return ROOM_ERROR_CODE, (f"The guest is checked-in to room {room_number}, and that room is not free "
                                         f"for {number_of_guests} guests from {arrival_date} to {leaving_date}")
            room_number = search_available_room(number_of_guests, new_date_range)
            if room_number == 0:
                DB_CON.rollback()  # put the old dates back
                return ROOM_ERROR_CODE, f"No room available for {number_of_guests} guests from {arrival_date} to {leaving_date}"
        create_date_range_in_db(order_id, room_number, new_date_range)  # Create new date_range
    update_q = "UPDATE orders SET customer_name=%s, number_of_guests =%s, room_number=%s, breakfast =%s, lunch =%s, dinner =%s, electric_car =%s, pet =%s where id=%s "
    params = (customer_name, number_of_guests, room_number, breakfast, lunch, dinner, electric_car, pet, order_id)
    DB_CURSER.execute(update_q, params)
    activity_log.log_activity("order_updated",
                              f"Order #{str(order_id).zfill(8)} updated ({customer_name}, room {room_number}, "
                              f"{arrival_date} → {leaving_date})", actor=session.current.username)
    DB_CON.commit()
    return UPDATE_ORDER_CODE, f"Update order {order_id} successfully "

# =================================================================================================================================
# --------------------------------------------------------------------------------------------------------------------------------------------
# ====================================================section 1 - add new order====================================================
# A room is free for a stay when it has no faults and none of its bookings overlap the stay. The leaving day is the
# check-out day, so a new guest can arrive on the day another one leaves. Dates are stored as dd/mm/yyyy text, so
# they are compared with to_date() - comparing the text itself puts "02/01/2027" before "15/12/2026".
_FREE_ROOMS_SQL = """
    SELECT r.room_number FROM rooms r
    WHERE r.room_capacity >= %(guests)s
        AND NOT EXISTS (SELECT 1 FROM rooms_faults rf WHERE rf.room_number = r.room_number)
        AND NOT EXISTS (SELECT 1 FROM dates_range dr WHERE dr.room_number = r.room_number
            AND to_date(dr.start_date, 'DD/MM/YYYY') < to_date(%(leaving)s, 'DD/MM/YYYY')
            AND to_date(dr.end_date, 'DD/MM/YYYY') > to_date(%(arrival)s, 'DD/MM/YYYY'))"""

def _free_rooms_params(guests_num, date_range):
    return {"guests": guests_num, "arrival": date_range.get_arrival_date(), "leaving": date_range.get_leaving_date()}

def search_available_room(guests_num, date_range):
    """The lowest-numbered free room for the stay, or 0 if there is none"""
    DB_CURSER.execute(_FREE_ROOMS_SQL + " ORDER BY r.room_number LIMIT 1", _free_rooms_params(guests_num, date_range))
    room = DB_CURSER.fetchone()
    return room[0] if room else 0

def is_room_available(room_number, guests_num, date_range):
    """Is this specific room free for the stay?"""
    DB_CURSER.execute(_FREE_ROOMS_SQL + " AND r.room_number = %(room)s",
                      dict(_free_rooms_params(guests_num, date_range), room=room_number))
    return DB_CURSER.fetchone() is not None

@rollback_on_error
def create_new_order_in_db(customer_name: str = None, guests: int = None, breakfast: bool = False, lunch: bool = False,
                           dinner: bool = False, electric_car: bool = False,
                           pet: bool = False, arrival_date: str = None, leaving_date: str = None):
    """
    Get data of the order and create new one and add to the ORDERS list

    :return: Error if there is one
    """
    if (
            customer_name == None or guests == None or arrival_date == None or leaving_date == None):
        return VERABLE_ERROR_CODE, "Please fill all the fields"
    try:
        # print("------------------Start create order------------------")
        if guests < 1:  # check if the guests number is ok
            return VERABLE_ERROR_CODE, "Can be 0 guests"
        order_dates_range = Dates_Range(arrival_date, leaving_date)  # create date range for the order
        if not order_dates_range.range_ok:  # check if there is a error in the date range
            return VERABLE_ERROR_CODE, order_dates_range.error_text
        room = search_available_room(
            guests, order_dates_range
        )  # look for available room
        if room == 0:
            return ROOM_ERROR_CODE, "No room available"
        # create the order
        order_info = [
            customer_name,
            guests,
            room,
            breakfast,
            lunch,
            dinner,
            electric_car,
            pet,
            datetime.now().strftime("%H:%M:%S - %d/%m/%Y"),
            session.current.username or "Unknown",
        ]
        order_id = create_order_in_db(order_info)
        # customer_name,number_of_guests,room_number, breakfast ,lunch ,dinner ,electric_car ,pet ,create_time ,create_by
        create_date_range_in_db(order_id, room, order_dates_range)  # create date-range for room and order
        activity_log.log_activity("order_created",
                                  f"Order #{str(order_id).zfill(8)} created for {customer_name} ({guests} guests, "
                                  f"room {room}, {arrival_date} → {leaving_date})", actor=session.current.username)
        DB_CON.commit()  # the order, its dates and the log row are saved together
        return OK_CODE, f"Order created successfully - {order_id}"
    except KeyboardInterrupt:
        exit()
        return ERROR_CODE, "keyboard error"

# ==================================================================================================================================
