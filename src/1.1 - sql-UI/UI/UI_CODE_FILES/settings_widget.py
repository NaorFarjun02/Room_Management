from datetime import datetime

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi

from models import *
from UI import theme


class Settings_Widget(QWidget):
    """Account details of the connected user + log out"""

    def __init__(self, widget):
        """init function that set al the main stuff of th page like UI and clicked event"""
        super(Settings_Widget, self).__init__()
        loadUi("UI/UI_Files/settings_widget.ui", self)  # load the UI of the page
        self.widget = widget  # the widget-stack that has all widgets --> so I can move to any other widget
        self.session_start = datetime.now()  # the app has no login yet, so the session starts when the app opens

        self.logout_btn.setIcon(theme.icon("check_out", theme.COLORS["danger"], 18))
        self.logout_btn.setIconSize(QSize(18, 18))
        self.logout_btn.clicked.connect(self.logout)

        self.display_account()

    def display_account(self):
        user_name = str(CURRENT_USER)
        role = "Front desk"
        self.avatar_label.setText(user_name[:1].upper())
        self.user_name_label.setText(user_name)
        self.user_role_label.setText(role)
        self.user_name_value.setText(user_name)
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
        # there is no login system in the app yet - the button is ready for when there will be one
        pass
