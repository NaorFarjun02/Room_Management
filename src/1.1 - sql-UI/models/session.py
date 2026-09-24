"""
The user that is currently logged in to this run of the app.

Import the module and read through it - `from models import session` then `session.current.username` -
never `from .session import current`, which would copy the reference at import time and go stale the
moment someone logs in or out (the same trap the old CURRENT_USER constant had).
"""


class Session:
    def __init__(self):
        self.user_id = None
        self.username = None
        self.full_name = None
        self.role = None  # "manager" or "desk"

    def login(self, user):
        """user: a dict as returned by auth.authenticate() / auth.list_users() (id, username, full_name, role, ...)"""
        self.user_id = user["id"]
        self.username = user["username"]
        self.full_name = user["full_name"]
        self.role = user["role"]

    def logout(self):
        self.__init__()

    def is_logged_in(self):
        return self.user_id is not None

    def is_manager(self):
        return self.role == "manager"

    def display_name(self):
        return self.full_name or self.username or ""


current = Session()  # the one session for this run of the app
