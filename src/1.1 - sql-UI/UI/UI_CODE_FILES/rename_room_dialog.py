from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi

from models import *


class Rename_Room_Dialog(QDialog):
    """Set or clear a room's optional display name"""

    def __init__(self, room_number, current_name=None):
        super(Rename_Room_Dialog, self).__init__()
        loadUi("UI/UI_Files/rename_room_dialog.ui", self)  # load the UI of the page
        self.room_number = room_number
        self.saved = False

        self.room_number_label.setText(f"Room {room_number}")
        if current_name:
            self.name_input.setText(current_name)

        self.save_btn.clicked.connect(self.save)
        self.cancel_btn.clicked.connect(self.reject)
        self.name_input.setFocus()

    def save(self):
        self.error_label.setText("")
        code, msg = set_room_name_db(self.room_number, self.name_input.text())
        if code != OK_CODE:
            self.error_label.setText(msg)
            return
        self.saved = True
        self.accept()
