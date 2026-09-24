from datetime import datetime

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QFrame, QPushButton
from PyQt5.uic import loadUi

from models import *
from models import auth, session, activity_log
from UI import theme
from .components import cell, pill_holder, table_header, table_row_layout, fixed_cell
from .user_dialog import User_Dialog

USERS_COLUMNS_TITLES = ["NAME", "USERNAME", "ROLE", "STATUS", "LAST LOGIN"]
USERS_COLUMNS_WIDTH = [170, 130, 90, 100, 170]

ACTIVITY_COLUMNS_TITLES = ["TIME", "TYPE", "ACTOR"]
ACTIVITY_COLUMNS_WIDTH = [110, 160, 120]


class Settings_Widget(QWidget):
    """Account details + change password (everyone), user management + activity log (managers only)"""

    def __init__(self, widget):
        """init function that set al the main stuff of th page like UI and clicked event"""
        super(Settings_Widget, self).__init__()
        loadUi("UI/UI_Files/settings_widget.ui", self)  # load the UI of the page
        self.widget = widget  # the widget-stack that has all widgets --> so I can move to any other widget
        self.session_start = datetime.now()  # when this login started

        self.logout_btn.setIcon(theme.icon("check_out", theme.COLORS["danger"], 18))
        self.logout_btn.setIconSize(QSize(18, 18))
        self.logout_btn.clicked.connect(self.logout)

        self.change_password_btn.clicked.connect(self.change_password)

        self.is_manager = session.current.is_manager()
        self.users_card.setVisible(self.is_manager)
        self.activity_card.setVisible(self.is_manager)
        if self.is_manager:
            self.users_table_header_layout.addWidget(table_header(USERS_COLUMNS_TITLES, USERS_COLUMNS_WIDTH,
                                                                   trailing_width=200))
            self.add_user_btn.setIcon(theme.icon("plus", "#FFFFFF", 16))
            self.add_user_btn.setIconSize(QSize(16, 16))
            self.add_user_btn.clicked.connect(self.add_user)
            self.setup_activity_log()

        self.display_account()

    def showEvent(self, event):
        # every time the settings page is shown, refresh the live data
        super(Settings_Widget, self).showEvent(event)
        if self.is_manager:
            self.refresh_users()
            self.refresh_activity()

    #################################### account ####################################
    def display_account(self):
        user_name = session.current.display_name()
        role = "Manager" if session.current.is_manager() else "Front desk"
        self.avatar_label.setText(user_name[:1].upper() if user_name else "?")
        self.user_name_label.setText(user_name)
        self.user_role_label.setText(role)
        self.user_name_value.setText(session.current.username or "-")
        self.role_value.setText(role)
        self.session_start_value.setText(self.session_start.strftime("%H:%M  ·  %d/%m/%Y"))
        self.database_value.setText(self.database_description())

    def database_description(self):
        try:
            info = DB_CON.info
            return f"{info.dbname} on {info.host}:{info.port}"
        except Exception:
            return "Connected"

    def logout(self):
        self.widget.window().relogin()  # relogin() lives on Main_Page; .window() walks up to it

    #################################### change my password ####################################
    def change_password(self):
        self.set_password_message("", "error")
        current_pw = self.current_password_input.text()
        new_pw = self.new_password_input.text()
        confirm_pw = self.confirm_new_password_input.text()
        if new_pw != confirm_pw:
            self.set_password_message("New passwords don't match", "error")
            return
        code, msg = auth.change_own_password(current_pw, new_pw)
        if code != OK_CODE:
            self.set_password_message(msg, "error")
            return
        self.set_password_message(msg, "success")
        for field in (self.current_password_input, self.new_password_input, self.confirm_new_password_input):
            field.setText("")

    def set_password_message(self, text, role):
        self.password_message_label.setText(text)
        theme.set_role(self.password_message_label, role)

    #################################### users (manager only) ####################################
    def clear_users_table(self):
        for i in reversed(range(self.users_widget.count())):
            self.users_widget.itemAt(i).widget().setParent(None)

    def refresh_users(self):
        self.clear_users_table()
        users = auth.list_users()
        for user in users:
            self.users_widget.addWidget(self.create_user_row(user))
        self.users_count_label.setText(f"{len(users)} users")

    def create_user_row(self, user):
        row = QFrame(self)
        row.setProperty("row", "true")
        row.setFixedHeight(58)
        layout = table_row_layout(row)

        display_name = user["full_name"] + ("  (you)" if user["id"] == session.current.user_id else "")
        layout.addWidget(cell(display_name, USERS_COLUMNS_WIDTH[0], "cell_strong"))
        layout.addWidget(cell(user["username"], USERS_COLUMNS_WIDTH[1]))
        layout.addWidget(cell("Manager" if user["role"] == "manager" else "Desk", USERS_COLUMNS_WIDTH[2]))
        layout.addWidget(pill_holder("Active" if user["is_active"] else "Disabled",
                                     "success" if user["is_active"] else "neutral", USERS_COLUMNS_WIDTH[3]))
        last_login = user["last_login"].strftime("%d/%m/%Y %H:%M") if user["last_login"] else "Never"
        layout.addWidget(cell(last_login, USERS_COLUMNS_WIDTH[4]))
        layout.addStretch()

        edit_btn = QPushButton(" Edit", row)
        edit_btn.setProperty("variant", "link")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setIcon(theme.icon("edit", theme.COLORS["accent"], 16))
        edit_btn.setIconSize(QSize(16, 16))
        edit_btn.clicked.connect(lambda: self.edit_user(user["id"]))
        layout.addWidget(fixed_cell(edit_btn, 84))

        if user["id"] != session.current.user_id:  # you can never disable / enable your own account
            toggle_btn = QPushButton(" Disable" if user["is_active"] else " Enable", row)
            toggle_btn.setProperty("variant", "link")
            toggle_btn.setCursor(Qt.PointingHandCursor)
            if user["is_active"]:
                toggle_btn.setProperty("tone", "danger")
                toggle_btn.setIcon(theme.icon("close", theme.COLORS["danger"], 16))
            else:
                toggle_btn.setIcon(theme.icon("check", theme.COLORS["accent"], 16))
            toggle_btn.setIconSize(QSize(16, 16))
            toggle_btn.clicked.connect(lambda: self.toggle_user(user))
            layout.addWidget(fixed_cell(toggle_btn, 116))
        else:
            layout.addSpacing(116)

        return row

    def add_user(self):
        dialog = User_Dialog()
        dialog.exec_()
        if dialog.saved:
            self.refresh_users()

    def edit_user(self, user_id):
        user = auth.get_user(user_id)
        dialog = User_Dialog(user)
        dialog.exec_()
        if dialog.saved:
            self.refresh_users()
            self.display_account()  # in case you just edited yourself

    def toggle_user(self, user):
        action = "disable" if user["is_active"] else "enable"
        question = MSG_Dialog(f"{action.capitalize()} user '{user['username']}'?", "Yes", "No")
        question.exec_()
        if question.status != "Yes":
            return
        code, msg = auth.set_user_active(user["id"], not user["is_active"])
        if code != OK_CODE:
            MSG_Popup(msg).exec_()
            return
        self.refresh_users()

    #################################### activity log (manager only) ####################################
    def setup_activity_log(self):
        self.activity_table_header_layout.addWidget(
            table_header(ACTIVITY_COLUMNS_TITLES, ACTIVITY_COLUMNS_WIDTH, stretch_title="DETAILS"))
        self.activity_search_input.textChanged.connect(self.refresh_activity)

        self.activity_filter = "all"
        self.activity_filter_buttons = {}
        for key, label in activity_log.GROUPS.items():
            btn = QPushButton(label, self)
            btn.setProperty("variant", "chip")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self.set_activity_filter(k))
            self.activity_filters_layout.addWidget(btn)
            self.activity_filter_buttons[key] = btn
        self.activity_filters_layout.addStretch()
        self.mark_selected_activity_filter()

    def set_activity_filter(self, filter_key):
        self.activity_filter = filter_key if filter_key in activity_log.GROUPS else "all"
        self.mark_selected_activity_filter()
        self.refresh_activity()

    def mark_selected_activity_filter(self):
        for key, btn in self.activity_filter_buttons.items():
            theme.set_selected(btn, key == self.activity_filter)

    def clear_activity_table(self):
        for i in reversed(range(self.activity_widget.count())):
            self.activity_widget.itemAt(i).widget().setParent(None)

    def refresh_activity(self):
        self.clear_activity_table()
        counts = activity_log.count_by_group()
        for key, btn in self.activity_filter_buttons.items():
            btn.setText(f"{activity_log.GROUPS[key]}  {counts.get(key, 0)}")

        rows = activity_log.get_activity_log(group=self.activity_filter, search=self.activity_search_input.text())
        for row in rows:
            self.activity_widget.addWidget(self.create_activity_row(row))
        if len(rows) == 0:
            empty_text = "No activity matches this search" if self.activity_search_input.text().strip() else "Nothing here yet"
            empty_label = cell(empty_text, role="muted")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setMinimumHeight(100)
            self.activity_widget.addWidget(empty_label)

    def create_activity_row(self, row):
        created_at, category, actor, summary = row
        frame = QFrame(self)
        frame.setProperty("row", "true")
        frame.setMinimumHeight(52)
        layout = table_row_layout(frame)
        layout.setContentsMargins(24, 10, 16, 10)

        layout.addWidget(cell(created_at.strftime("%d/%m  %H:%M"), ACTIVITY_COLUMNS_WIDTH[0]))
        tone = activity_log.GROUP_TONE.get(activity_log.category_group(category), "neutral")
        layout.addWidget(pill_holder(activity_log.category_label(category), tone, ACTIVITY_COLUMNS_WIDTH[1]))
        layout.addWidget(cell(actor or "-", ACTIVITY_COLUMNS_WIDTH[2]))
        summary_label = cell(summary)
        summary_label.setWordWrap(True)
        layout.addWidget(summary_label, 1)

        return frame
