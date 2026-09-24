"""
The user that is currently logged in to this run of the app.

Import the module and read through it - `from models import session` then `session.current.username` -
never `from .session import current`, which would copy the reference at import time and go stale the
moment someone logs in or out (the same trap the old CURRENT_USER constant had).
"""
from . import activity_log


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

    def logout(self, reason="logout"):
        """reason: "logout" (the Log out button) or "auto_lock" (the idle timer) - logged either way"""
        if self.is_logged_in():
            summary = (f"{self.display_name()} signed out" if reason == "logout"
                      else f"{self.display_name()} was auto-locked out after being idle")
            activity_log.log_activity(reason if reason in ("logout", "auto_lock") else "logout", summary,
                                      actor=self.username)
        self.__init__()

    def is_logged_in(self):
        return self.user_id is not None

    def is_manager(self):
        return self.role == "manager"

    def display_name(self):
        return self.full_name or self.username or ""


current = Session()  # the one session for this run of the app
