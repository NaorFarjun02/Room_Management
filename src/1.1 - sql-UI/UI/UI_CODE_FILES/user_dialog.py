from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi

from models import *
from models import auth


class User_Dialog(QDialog):
    """Create a new user (user=None) or edit an existing one (user= a dict from auth.list_users())"""

    def __init__(self, user=None):
        super(User_Dialog, self).__init__()
        loadUi("UI/UI_Files/user_dialog.ui", self)  # load the UI of the page
        self.user = user
        self.saved = False  # set to True once a save actually went through

        self.role_combo.addItem("Manager", "manager")
        self.role_combo.addItem("Desk", "desk")

        if user is None:
            self.title_label.setText("Add user")
            self.subtitle_label.setText("Create a new account")
            self.password_hint_label.setText("At least 8 characters")
        else:
            self.title_label.setText("Edit user")
            self.subtitle_label.setText(f"Editing {user['username']}")
            self.full_name_input.setText(user["full_name"])
            self.username_input.setText(user["username"])
            self.role_combo.setCurrentIndex(self.role_combo.findData(user["role"]))
            self.password_hint_label.setText("Leave both password fields empty to keep the current password")

        self.save_btn.clicked.connect(self.save)
        self.cancel_btn.clicked.connect(self.reject)
        self.full_name_input.setFocus()

    def save(self):
        self.error_label.setText("")
        full_name = self.full_name_input.text().strip()
        username = self.username_input.text().strip()
        role = self.role_combo.currentData()
        password = self.password_input.text()
        confirm = self.confirm_password_input.text()

        if password or confirm:
            if password != confirm:
                self.error_label.setText("Passwords don't match")
                return
        elif self.user is None:
            self.error_label.setText("Password is required")
            return

        if self.user is None:
            code, msg = auth.create_user(full_name, username, role, password)
        else:
            code, msg = auth.update_user(self.user["id"], full_name=full_name, username=username, role=role,
                                         password=password or None)
        if code != OK_CODE:
            self.error_label.setText(msg)
            return
        self.saved = True
        self.accept()
