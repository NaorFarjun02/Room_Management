from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi

from UI import theme
from models import auth, session, OK_CODE

LOGIN_PAGE, FIRST_RUN_PAGE = 0, 1


class Login_Dialog(QDialog):
    """Shown before the main window. Two modes, picked automatically:
    - normal login (username + password)
    - first run (no users exist yet) - create the first account, which is always a manager
    On success it logs the session in (session.current.login(...)) and accepts the dialog."""

    def __init__(self):
        super(Login_Dialog, self).__init__()
        loadUi("models/dialogs/login_dialog/login_dialog.ui", self)  # load the UI of the page
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.brand_mark.setText("RM")

        self.login_stack.setCurrentIndex(FIRST_RUN_PAGE if not auth.has_any_user() else LOGIN_PAGE)

        self.login_btn.clicked.connect(self.try_login)
        self.login_username_input.returnPressed.connect(self.try_login)
        self.login_password_input.returnPressed.connect(self.try_login)

        self.first_run_btn.clicked.connect(self.try_create_first_manager)
        for field in (self.first_run_fullname_input, self.first_run_username_input,
                     self.first_run_password_input, self.first_run_confirm_input):
            field.returnPressed.connect(self.try_create_first_manager)

        if self.login_stack.currentIndex() == LOGIN_PAGE:
            self.login_username_input.setFocus()
        else:
            self.first_run_fullname_input.setFocus()

    def try_login(self):
        self.login_error_label.setText("")
        username = self.login_username_input.text()
        password = self.login_password_input.text()
        code, result = auth.authenticate(username, password)
        if code != OK_CODE:
            self.login_error_label.setText(result)
            return
        session.current.login(result)
        self.accept()

    def try_create_first_manager(self):
        self.first_run_error_label.setText("")
        full_name = self.first_run_fullname_input.text()
        username = self.first_run_username_input.text()
        password = self.first_run_password_input.text()
        confirm = self.first_run_confirm_input.text()
        if password != confirm:
            self.first_run_error_label.setText("Passwords don't match")
            return
        code, result = auth.create_first_manager(full_name, username, password)
        if code != OK_CODE:
            self.first_run_error_label.setText(result)
            return
        session.current.login(result)
        self.accept()
