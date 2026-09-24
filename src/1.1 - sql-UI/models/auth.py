"""
Users, passwords and permissions.

Two roles: "manager" (everything) and "desk" (front-desk work: orders and rooms, but not the
manager-only actions listed in MANAGER_ONLY_ACTIONS). Permission checks happen twice - the UI hides
buttons the current user can't use, and every sensitive database function is wrapped with
@require_permission so a hidden button is not the only thing stopping the action.
"""
import functools
import hashlib
import hmac
import os
import time

from .global_ver import DB_CON, DB_CURSER, OK_CODE, ERROR_CODE
from . import session

ROLES = ("manager", "desk")

# actions only a manager may do; everything else, a logged-in user (any role) may do
MANAGER_ONLY_ACTIONS = {
    "add_room",
    "delete_room",
    "rename_room",
    "delete_order",
    "manage_users",
}

MIN_PASSWORD_LENGTH = 8
_PBKDF2_ITERATIONS = 260_000

_MAX_FAILED_ATTEMPTS = 5
_LOCKOUT_SECONDS = 60
_failed_attempts = {}  # username.lower() -> [count, locked_until_timestamp]


########################################## passwords ##########################################
def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored_hash):
    try:
        algo, iterations, salt_hex, hash_hex = stored_hash.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(digest.hex(), hash_hex)
    except Exception:
        return False


########################################## permissions ##########################################
def can(action, role=None):
    """Can the given role (default: the logged-in user's role) do this action?"""
    role = role if role is not None else (session.current.role if session.current.is_logged_in() else None)
    if role == "manager":
        return True
    if role == "desk":
        return action not in MANAGER_ONLY_ACTIONS
    return False


def require_permission(action):
    """Decorator for a database function: refuses to run it (and logs nothing) unless the logged-in
    user may do `action`. Wrapped functions must return an (code, message) tuple on every path."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not can(action):
                who = session.current.display_name() or "This user"
                return ERROR_CODE, f"{who} doesn't have permission to do this."
            return func(*args, **kwargs)
        return wrapper
    return decorator


########################################## reading users ##########################################
def _row_to_user(row):
    if row is None:
        return None
    keys = ["id", "username", "full_name", "role", "password_hash", "is_active", "created_at", "last_login"]
    return dict(zip(keys, row))


def get_user(user_id):
    DB_CURSER.execute("""SELECT id, username, full_name, role, password_hash, is_active, created_at, last_login
        FROM users WHERE id = %s""", (user_id,))
    return _row_to_user(DB_CURSER.fetchone())


def get_user_by_username(username):
    DB_CURSER.execute("""SELECT id, username, full_name, role, password_hash, is_active, created_at, last_login
        FROM users WHERE lower(username) = lower(%s)""", (username,))
    return _row_to_user(DB_CURSER.fetchone())


def list_users():
    """Every user, without their password hash, ordered by full name"""
    DB_CURSER.execute("""SELECT id, username, full_name, role, is_active, created_at, last_login
        FROM users ORDER BY full_name""")
    keys = ["id", "username", "full_name", "role", "is_active", "created_at", "last_login"]
    return [dict(zip(keys, row)) for row in DB_CURSER.fetchall()]


def has_any_user():
    DB_CURSER.execute("SELECT 1 FROM users LIMIT 1")
    return DB_CURSER.fetchone() is not None


def active_manager_count(exclude_id=None):
    DB_CURSER.execute("SELECT COUNT(*) FROM users WHERE role = 'manager' AND is_active AND id <> %s",
                      (exclude_id if exclude_id is not None else -1,))
    return DB_CURSER.fetchone()[0]


########################################## login ##########################################
def _is_locked_out(username):
    entry = _failed_attempts.get(username.lower())
    if not entry:
        return 0
    remaining = entry[1] - time.time()
    return max(0, int(remaining))


def _record_failed_attempt(username):
    key = username.lower()
    count, _ = _failed_attempts.get(key, (0, 0))
    count += 1
    locked_until = time.time() + _LOCKOUT_SECONDS if count >= _MAX_FAILED_ATTEMPTS else 0
    _failed_attempts[key] = (count, locked_until)


def _clear_failed_attempts(username):
    _failed_attempts.pop(username.lower(), None)


def authenticate(username, password):
    """(OK_CODE, user dict) on success, (ERROR_CODE, message) otherwise. Does not touch the session -
    the caller logs the session in with session.current.login(user) after a successful call."""
    username = (username or "").strip()
    if not username or not password:
        return ERROR_CODE, "Enter a username and password"

    locked_for = _is_locked_out(username)
    if locked_for > 0:
        return ERROR_CODE, f"Too many failed attempts - try again in {locked_for} seconds"

    user = get_user_by_username(username)
    if user is None or not verify_password(password, user["password_hash"]):
        _record_failed_attempt(username)
        return ERROR_CODE, "Wrong username or password"
    if not user["is_active"]:
        return ERROR_CODE, "This account is disabled"

    _clear_failed_attempts(username)
    DB_CURSER.execute("UPDATE users SET last_login = now() WHERE id = %s", (user["id"],))
    DB_CON.commit()
    user["last_login"] = None  # stale value from before the update; callers that need it can re-fetch
    return OK_CODE, user


def change_own_password(current_password, new_password):
    """Any logged-in user may change their own password - unlike update_user, this needs no manage_users
    permission, only the current password."""
    if not session.current.is_logged_in():
        return ERROR_CODE, "You must be logged in"
    user = get_user(session.current.user_id)
    if user is None or not verify_password(current_password, user["password_hash"]):
        return ERROR_CODE, "Current password is wrong"
    if len(new_password) < MIN_PASSWORD_LENGTH:
        return ERROR_CODE, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    DB_CURSER.execute("UPDATE users SET password_hash = %s WHERE id = %s", (hash_password(new_password), user["id"]))
    DB_CON.commit()
    return OK_CODE, "Password updated"


########################################## creating / changing users ##########################################
def _validate_user_fields(full_name, username, role, password):
    if not full_name or not full_name.strip():
        return "Full name can't be empty"
    if not username or not username.strip():
        return "Username can't be empty"
    if role not in ROLES:
        return "Role must be manager or desk"
    if password is not None and len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    return None


def create_first_manager(full_name, username, password):
    """Creates the very first user (a manager) and logs them in. Only works while there are no users
    at all, so it can't be used to slip in a new manager once the app has real accounts."""
    if has_any_user():
        return ERROR_CODE, "Setup is already done - use the login screen"
    error = _validate_user_fields(full_name, username, "manager", password)
    if error:
        return ERROR_CODE, error
    DB_CURSER.execute("""INSERT INTO users (username, full_name, role, password_hash)
        VALUES (%s, %s, 'manager', %s) RETURNING id, username, full_name, role, is_active, created_at, last_login""",
        (username.strip(), full_name.strip(), hash_password(password)))
    row = DB_CURSER.fetchone()
    DB_CON.commit()
    keys = ["id", "username", "full_name", "role", "is_active", "created_at", "last_login"]
    return OK_CODE, dict(zip(keys, row))


@require_permission("manage_users")
def create_user(full_name, username, role, password):
    error = _validate_user_fields(full_name, username, role, password)
    if error:
        return ERROR_CODE, error
    if get_user_by_username(username) is not None:
        return ERROR_CODE, f"Username '{username}' is already taken"
    DB_CURSER.execute("""INSERT INTO users (username, full_name, role, password_hash) VALUES (%s, %s, %s, %s)
        RETURNING id""", (username.strip(), full_name.strip(), role, hash_password(password)))
    user_id = DB_CURSER.fetchone()[0]
    DB_CON.commit()
    return OK_CODE, f"User '{username}' created"


@require_permission("manage_users")
def update_user(user_id, full_name=None, username=None, role=None, password=None):
    """Fields left as None keep their current value. Password is only changed when given."""
    user = get_user(user_id)
    if user is None:
        return ERROR_CODE, "User not found"
    full_name = full_name if full_name is not None else user["full_name"]
    username = username if username is not None else user["username"]
    role = role if role is not None else user["role"]
    error = _validate_user_fields(full_name, username, role, password)
    if error:
        return ERROR_CODE, error
    other = get_user_by_username(username)
    if other is not None and other["id"] != user_id:
        return ERROR_CODE, f"Username '{username}' is already taken"
    if user["role"] == "manager" and role != "manager" and active_manager_count(exclude_id=user_id) == 0:
        return ERROR_CODE, "Can't change the role of the last manager"

    if password:
        DB_CURSER.execute("UPDATE users SET full_name=%s, username=%s, role=%s, password_hash=%s WHERE id=%s",
                          (full_name.strip(), username.strip(), role, hash_password(password), user_id))
    else:
        DB_CURSER.execute("UPDATE users SET full_name=%s, username=%s, role=%s WHERE id=%s",
                          (full_name.strip(), username.strip(), role, user_id))
    DB_CON.commit()
    if session.current.user_id == user_id:  # keep the session in sync if you edited your own account
        session.current.login({"id": user_id, "username": username.strip(), "full_name": full_name.strip(), "role": role})
    return OK_CODE, f"User '{username}' updated"


@require_permission("manage_users")
def set_user_active(user_id, is_active):
    """Disable (is_active=False) or re-enable a user. A disabled user can't log in, but their name
    stays on their past orders and log entries."""
    user = get_user(user_id)
    if user is None:
        return ERROR_CODE, "User not found"
    if not is_active:
        if user_id == session.current.user_id:
            return ERROR_CODE, "You can't disable your own account"
        if user["role"] == "manager" and active_manager_count(exclude_id=user_id) == 0:
            return ERROR_CODE, "Can't disable the last manager"
    DB_CURSER.execute("UPDATE users SET is_active = %s WHERE id = %s", (is_active, user_id))
    DB_CON.commit()
    return OK_CODE, f"User '{user['username']}' {'enabled' if is_active else 'disabled'}"
