"""
The audit trail: every action a user takes in the app, who did it and when.

Stored as rows in the activity_log table (not the old free-text log file), so it can actually be
filtered and searched. Every call site passes its own `actor` (usually session.current.username) -
this module doesn't read the session itself, so it has no dependency on session.py and can be
imported from anywhere (models/session.py included) without a circular import.
"""
from .global_ver import DB_CURSER

# category -> (human label for the pill, filter group)
CATEGORIES = {
    "login": ("Signed in", "account"),
    "logout": ("Signed out", "account"),
    "auto_lock": ("Auto-locked (idle)", "account"),
    "password_changed": ("Password changed", "account"),

    "user_created": ("User created", "users"),
    "user_updated": ("User updated", "users"),
    "user_disabled": ("User disabled", "users"),
    "user_enabled": ("User enabled", "users"),

    "order_created": ("Order created", "orders"),
    "order_updated": ("Order updated", "orders"),
    "order_deleted": ("Order deleted", "orders"),
    "check_in": ("Checked in", "orders"),
    "check_in_cancelled": ("Check-in cancelled", "orders"),
    "check_out": ("Checked out", "orders"),
    "check_out_cancelled": ("Check-out cancelled", "orders"),

    "room_created": ("Room created", "rooms"),
    "room_deleted": ("Room deleted", "rooms"),
    "room_renamed": ("Room renamed", "rooms"),
    "room_marked_clean": ("Room marked clean", "rooms"),
    "fault_added": ("Fault reported", "rooms"),
    "fault_resolved": ("Fault resolved", "rooms"),
}

# the filter chips on the Settings > Activity log card, in display order
GROUPS = {
    "all": "All activity",
    "account": "Account",
    "orders": "Orders",
    "rooms": "Rooms",
    "users": "Users",
}

GROUP_TONE = {"account": "neutral", "orders": "info", "rooms": "success", "users": "accent"}


def category_label(category):
    return CATEGORIES.get(category, (category, "account"))[0]


def category_group(category):
    return CATEGORIES.get(category, (category, "account"))[1]


def log_activity(category, summary, actor):
    """Record one row. actor is the username responsible (never read from the session here - pass it in).
    Does not commit: the caller commits once, so the action and its log row are saved (or rolled back) together."""
    DB_CURSER.execute("INSERT INTO activity_log (category, actor, summary) VALUES (%s, %s, %s)",
                      (category, actor or "system", summary))


def _can_view_log():
    from . import auth  # imported here: auth imports this module, so a top-level import would be circular
    return auth.can("view_activity_log")


def get_activity_log(group="all", search="", limit=300):
    """Most recent first, optionally narrowed to one filter group and/or a free-text search"""
    if not _can_view_log():
        return []
    sql = "SELECT created_at, category, actor, summary FROM activity_log"
    conditions, params = [], []
    if group != "all":
        categories = [c for c in CATEGORIES if category_group(c) == group]
        conditions.append("category = ANY(%s)")
        params.append(categories)
    search = (search or "").strip()
    if search:
        conditions.append("(summary ILIKE %s OR actor ILIKE %s)")
        params += [f"%{search}%", f"%{search}%"]
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY created_at DESC, id DESC LIMIT %s"
    params.append(limit)
    DB_CURSER.execute(sql, params)
    return DB_CURSER.fetchall()


def count_by_group():
    """{"all": N, "account": N, "orders": N, "rooms": N, "users": N} for the filter chip counts"""
    if not _can_view_log():
        return {group: 0 for group in GROUPS}
    DB_CURSER.execute("SELECT category, COUNT(*) FROM activity_log GROUP BY category")
    per_category = dict(DB_CURSER.fetchall())
    counts = {"all": sum(per_category.values())}
    for group in GROUPS:
        if group == "all":
            continue
        counts[group] = sum(n for category, n in per_category.items() if category_group(category) == group)
    return counts
