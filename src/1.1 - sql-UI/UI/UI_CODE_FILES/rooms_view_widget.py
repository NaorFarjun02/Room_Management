from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QFrame, QLabel, QPushButton, QHBoxLayout
from PyQt5.uic import loadUi

from models import *
from models.dialogs.popup_msg import MSG_Popup
from models.dialogs.dialog_msg import MSG_Dialog
from .room_dates_catch_dialog import Dates_Catch_Dialog
from .room_faults_dialog import Faults_Dialog
from .new_room_dialog import New_Room_Dialog
from .new_room_fault_dialog import New_Fault_Dialog
from .components import cell, pill_holder
from UI import theme

COLUMNS_WIDTH = [120, 110, 150, 160, 130, 150]  # room, capacity, status, cleaning, faults, dates

class Room_View_Widget(QWidget):

    def __init__(self, widget):
        """init function that set al the main stuff of th page like UI and clicked event"""
        super(Room_View_Widget, self).__init__()
        loadUi("UI/UI_Files/rooms_view_widget.ui", self)  # load the UI of the page
        self.widget = widget  # the widget-stack that has all widgets --> so I can move to any other widget

        self.table_header_layout.addWidget(self.create_titles_frame())  # the header stays on top while the rows scroll
        self.new_room_btn.setIcon(theme.icon("plus", "#FFFFFF", 16))
        self.new_fault_btn.setIcon(theme.icon("wrench", theme.COLORS["text"], 16))
        self.home_btn.setIcon(theme.icon("arrow_left", theme.COLORS["text_muted"], 16))
        self.home_btn.clicked.connect(self.home)
        self.new_room_btn.clicked.connect(self.new_room)
        self.new_fault_btn.clicked.connect(self.new_fault)

    def home(self):
        """

		Go back to home page after clear the page from the current order that display
		"""
        self.clear_rooms_table()

        self.widget.setCurrentIndex(windows_indexes["home-menu"])  # return to home menu

    def new_room(self):
        """Create a new room and add it to the table"""

        new_room_dialog = New_Room_Dialog()
        new_room_dialog.exec_()
        if new_room_dialog.capacity < 1 or new_room_dialog.capacity > 15:
            return
        create_room_in_db(new_room_dialog.capacity)
        self.refresh_rooms_status()
    def new_fault(self):
        """Create a new room and add it to the table"""

        new_fault_dialog = New_Fault_Dialog()
        new_fault_dialog.exec_()
        add_new_room_fault(new_fault_dialog.room_number,new_fault_dialog.fault)
        self.refresh_rooms_status()
    def clear_rooms_table(self):

        for i in reversed(range(self.rooms_widget.count())):
            self.rooms_widget.itemAt(i).widget().setParent(None)

    def refresh_rooms_status(self):
        self.clear_rooms_table()
        try:
            rooms = get_rooms_from_db()
            for r in rooms:
                self.rooms_widget.addWidget(self.create_room_frame(r))
            self.rooms_count_label.setText(f"{len(rooms)} rooms  ·  {sum(1 for r in rooms if not r[2])} available now")
            if len(rooms) == 0:
                empty_label = cell("No rooms yet - use \"Add room\" to create the first one", role="muted")
                empty_label.setAlignment(Qt.AlignCenter)
                empty_label.setMinimumHeight(120)
                self.rooms_widget.addWidget(empty_label)
        except Exception as e:
            print(e)

    def row_layout(self, frame):
        """same margins / spacing for the header and for every room row so the columns line up"""
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(24, 0, 16, 0)
        layout.setSpacing(12)
        return layout

    def create_titles_frame(self):
        frame_titles = QFrame(self)
        frame_titles.setObjectName("table_header")
        frame_titles.setFixedHeight(46)
        layout = self.row_layout(frame_titles)
        for title, width in zip(["ROOM", "CAPACITY", "STATUS (NOW)", "CLEANING", "FAULTS", "BOOKED DATES"], COLUMNS_WIDTH):
            layout.addWidget(cell(title, width))
        layout.addStretch()
        layout.addSpacing(34)  # the delete button column
        return frame_titles

    def create_room_frame(self, room=None):
        if room is None:
            return None
        # room = (room_number, room_capacity, room_is_catch, room_is_clean)
        room_frame = QFrame(self)
        room_frame.setProperty("row", "true")
        room_frame.setFixedHeight(64)
        layout = self.row_layout(room_frame)

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

        faults_room = QPushButton(" Faults", room_frame)
        faults_room.setProperty("variant", "link")
        faults_room.setCursor(Qt.PointingHandCursor)
        faults_room.setIcon(theme.icon("wrench", theme.COLORS["accent"], 16))
        faults_room.setIconSize(QSize(16, 16))
        faults_room.setObjectName("room_faults")
        faults_room.clicked.connect(lambda: self.show_faults(room[0]))
        layout.addWidget(self.fixed_cell(faults_room, COLUMNS_WIDTH[4]))

        dates_catch_room = QPushButton(" Bookings", room_frame)
        dates_catch_room.setProperty("variant", "link")
        dates_catch_room.setCursor(Qt.PointingHandCursor)
        dates_catch_room.setIcon(theme.icon("calendar", theme.COLORS["accent"], 16))
        dates_catch_room.setIconSize(QSize(16, 16))
        dates_catch_room.setObjectName("room_dates_catch")
        dates_catch_room.clicked.connect(lambda: self.show_dates_catch(room[0]))
        layout.addWidget(self.fixed_cell(dates_catch_room, COLUMNS_WIDTH[5]))

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

    def fixed_cell(self, widget, width):
        holder = QFrame()
        holder.setFixedWidth(width)
        holder_layout = QHBoxLayout(holder)
        holder_layout.setContentsMargins(0, 0, 0, 0)
        holder_layout.addWidget(widget, 0, Qt.AlignLeft | Qt.AlignVCenter)
        return holder

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
        else:
            MSG_Popup("The room have no faults").exec_()
