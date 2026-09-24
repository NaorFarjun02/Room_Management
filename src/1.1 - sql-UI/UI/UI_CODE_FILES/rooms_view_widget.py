from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QFrame, QPushButton
from PyQt5.uic import loadUi

from models import *
from models.dialogs.popup_msg import MSG_Popup
from models.dialogs.dialog_msg import MSG_Dialog
from .room_dates_catch_dialog import Dates_Catch_Dialog
from .room_faults_dialog import Faults_Dialog
from .new_room_dialog import New_Room_Dialog
from .new_room_fault_dialog import New_Fault_Dialog
from .components import cell, pill_holder, table_header, table_row_layout, fixed_cell
from UI import theme

COLUMNS_TITLES = ["ROOM", "CAPACITY", "STATUS (NOW)", "CLEANING", "FAULTS", "BOOKED DATES"]
COLUMNS_WIDTH = [120, 110, 150, 160, 130, 150]  # room, capacity, status, cleaning, faults, dates

# the filters of the rooms table: key -> (button text, function that says if a room is in the filter)
# room = (room_number, room_capacity, occupied_now, room_is_clean, faults_count)
ROOMS_FILTERS = {
    "all": ("All rooms", lambda room: True),
    "free": ("Available now", lambda room: not room[2]),
    "catch": ("Occupied now", lambda room: room[2]),
    "dirty": ("Needs cleaning", lambda room: not room[3]),
}


class Room_View_Widget(QWidget):

    def __init__(self, widget):
        """init function that set al the main stuff of th page like UI and clicked event"""
        super(Room_View_Widget, self).__init__()
        loadUi("UI/UI_Files/rooms_view_widget.ui", self)  # load the UI of the page
        self.widget = widget  # the widget-stack that has all widgets --> so I can move to any other widget
        self.current_filter = "all"

        # the header stays on top while the rows scroll
        self.table_header_layout.addWidget(table_header(COLUMNS_TITLES, COLUMNS_WIDTH, trailing_width=34))
        self.new_room_btn.setIcon(theme.icon("plus", "#FFFFFF", 16))
        self.new_fault_btn.setIcon(theme.icon("wrench", theme.COLORS["text"], 16))
        self.home_btn.setIcon(theme.icon("arrow_left", theme.COLORS["text_muted"], 16))
        self.home_btn.clicked.connect(self.home)
        self.new_room_btn.clicked.connect(self.new_room)
        self.new_fault_btn.clicked.connect(self.new_fault)

        ############### filter buttons ###############
        self.filter_buttons = {}
        for key, (text, _) in ROOMS_FILTERS.items():
            btn = QPushButton(text, self)
            btn.setProperty("variant", "chip")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self.set_filter(k))
            self.filters_layout.addWidget(btn)
            self.filter_buttons[key] = btn
        self.filters_layout.addStretch()
        self.mark_selected_filter()

    def home(self):
        """

		Go back to home page after clear the page from the current order that display
		"""
        self.clear_rooms_table()

        self.widget.setCurrentIndex(windows_indexes["home-menu"])  # return to home menu

    def set_filter(self, filter_key="all"):
        """Show only the rooms that match the filter (all / free / catch / dirty)"""
        self.current_filter = filter_key if filter_key in ROOMS_FILTERS else "all"
        self.mark_selected_filter()
        self.refresh_rooms_status()

    def mark_selected_filter(self):
        for key, btn in self.filter_buttons.items():
            theme.set_selected(btn, key == self.current_filter)

    def new_room(self):
        """Create a new room and add it to the table, return True if a room was created"""

        new_room_dialog = New_Room_Dialog()
        new_room_dialog.exec_()
        if new_room_dialog.capacity < 1 or new_room_dialog.capacity > 15:
            return False
        create_room_in_db(new_room_dialog.capacity)
        self.refresh_rooms_status()
        return True

    def new_fault(self):
        """Add a fault to one of the rooms"""

        new_fault_dialog = New_Fault_Dialog()
        new_fault_dialog.exec_()
        if new_fault_dialog.room_number == 0:  # the dialog was canceled
            return
        add_new_room_fault(new_fault_dialog.room_number,new_fault_dialog.fault)
        self.refresh_rooms_status()

    def clear_rooms_table(self):

        for i in reversed(range(self.rooms_widget.count())):
            self.rooms_widget.itemAt(i).widget().setParent(None)

    def refresh_rooms_status(self):
        self.clear_rooms_table()
        try:
            rooms = get_rooms_status_from_db()
        except Exception as e:
            print(e)
            return
        for key, btn in self.filter_buttons.items():  # show how many rooms are in every filter
            text, in_filter = ROOMS_FILTERS[key]
            btn.setText(f"{text}  {sum(1 for r in rooms if in_filter(r))}")

        filter_text, in_filter = ROOMS_FILTERS[self.current_filter]
        self.title_label.setText(filter_text)
        rooms_to_show = [r for r in rooms if in_filter(r)]
        for r in rooms_to_show:
            self.rooms_widget.addWidget(self.create_room_frame(r))
        self.rooms_count_label.setText(f"{len(rooms)} rooms  ·  {sum(1 for r in rooms if not r[2])} available now")

        if len(rooms_to_show) == 0:
            if len(rooms) == 0:
                empty_text = "No rooms yet - use \"Add room\" to create the first one"
            else:
                empty_text = "No rooms match this filter"
            empty_label = cell(empty_text, role="muted")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setMinimumHeight(120)
            self.rooms_widget.addWidget(empty_label)

    def create_room_frame(self, room=None):
        if room is None:
            return None
        # room = (room_number, room_capacity, occupied_now, room_is_clean, faults_count)
        room_frame = QFrame(self)
        room_frame.setProperty("row", "true")
        room_frame.setFixedHeight(64)
        layout = table_row_layout(room_frame)

        layout.addWidget(cell(f"Room {room[0]}", COLUMNS_WIDTH[0], "cell_strong"))
        layout.addWidget(cell(f"{room[1]} guests", COLUMNS_WIDTH[1]))
        if room[2]:
            layout.addWidget(pill_holder("Occupied", "info", COLUMNS_WIDTH[2]))
        else:
            layout.addWidget(pill_holder("Available", "success", COLUMNS_WIDTH[2]))
        if room[3]:
            layout.addWidget(pill_holder("Clean", "success", COLUMNS_WIDTH[3]))
        else:
            layout.addWidget(pill_holder("Needs cleaning", "warning", COLUMNS_WIDTH[3]))

        faults_count = room[4]
        faults_room = QPushButton(f" Faults ({faults_count})" if faults_count else " No faults", room_frame)
        faults_room.setProperty("variant", "link")
        faults_room.setCursor(Qt.PointingHandCursor)
        if faults_count:
            faults_room.setIcon(theme.icon("alert", theme.COLORS["warning"], 16))
        else:
            faults_room.setIcon(theme.icon("check", theme.COLORS["success"], 16))
        faults_room.setIconSize(QSize(16, 16))
        faults_room.setObjectName("room_faults")
        faults_room.clicked.connect(lambda: self.show_faults(room[0]))
        layout.addWidget(fixed_cell(faults_room, COLUMNS_WIDTH[4]))

        dates_catch_room = QPushButton(" Bookings", room_frame)
        dates_catch_room.setProperty("variant", "link")
        dates_catch_room.setCursor(Qt.PointingHandCursor)
        dates_catch_room.setIcon(theme.icon("calendar", theme.COLORS["accent"], 16))
        dates_catch_room.setIconSize(QSize(16, 16))
        dates_catch_room.setObjectName("room_dates_catch")
        dates_catch_room.clicked.connect(lambda: self.show_dates_catch(room[0]))
        layout.addWidget(fixed_cell(dates_catch_room, COLUMNS_WIDTH[5]))

        layout.addStretch()
        delete_room_btn = QtWidgets.QPushButton(room_frame)
        delete_room_btn.setProperty("variant", "icon")
        delete_room_btn.setCursor(Qt.PointingHandCursor)
        delete_room_btn.setToolTip(f"Delete room {room[0]}")
        delete_room_btn.setIcon(theme.icon("trash", theme.COLORS["danger"], 18))
        delete_room_btn.setIconSize(QSize(18, 18))
        delete_room_btn.setObjectName("delete_room_btn")
        delete_room_btn.clicked.connect(lambda: self.delete_room(room[0]))
        layout.addWidget(delete_room_btn)

        return room_frame

    # -------------------------clicked event functions-------------------------

    def delete_room(self, room_number):
        delete_status = MSG_Dialog(f"Delete room number {room_number}", "Yes",
                                   "No")  # Check if the user really wants to delete the room
        delete_status.exec()
        if delete_status.status == "Yes":  # If the user really wants to delete the room
            room_dates = get_date_range_by_room_id_db(room_number=room_number)
            if len(room_dates) > 0:  # Check if the the room is not booked
                MSG_Popup("The room is reserved for future bookings, you can't delete it").exec()
                return
            delete_room_db(room_number)
            self.refresh_rooms_status()

    def show_dates_catch(self, room_number):
        room_dates_catch_list = get_date_range_by_room_id_db(room_number=room_number)
        if len(room_dates_catch_list) > 0:
            date_dialog = Dates_Catch_Dialog(room_number, room_dates_catch_list)
            date_dialog.exec()
        else:
            MSG_Popup("The room does not catch").exec_()

    def show_faults(self, room_number):
        room_faults_list = get_room_faults_from_db(room_number=room_number)
        if len(room_faults_list) > 0:
            fault_dialog=Faults_Dialog(room_number,room_faults_list)
            fault_dialog.exec_()
            self.refresh_rooms_status()  # faults may have been marked as fixed
        else:
            MSG_Popup("The room have no faults").exec_()
