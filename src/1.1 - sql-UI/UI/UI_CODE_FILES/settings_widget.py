from datetime import datetime

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QFrame, QPushButton
from PyQt5.uic import loadUi

from models import *
from models import auth, session
from UI import theme
from .components import cell, pill_holder, table_header, table_row_layout, fixed_cell
from .user_dialog import User_Dialog

USERS_COLUMNS_TITLES = ["NAME", "USERNAME", "ROLE", "STATUS", "LAST LOGIN"]
USERS_COLUMNS_WIDTH = [170, 130, 90, 100, 170]


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
            self.activity_filter_input.textChanged.connect(self.refresh_activity)

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
    def refresh_activity(self):
        try:
            lines = find_logger_by_number("1") or []
        except Exception as e:
            self.activity_log_view.setPlainText(f"Can't read the activity log: {e}")
            return
        needle = self.activity_filter_input.text().strip().lower()
        if needle:
            lines = [line for line in lines if needle in line.lower()]
        self.activity_log_view.setPlainText("\n".join(reversed(lines[-500:])))
