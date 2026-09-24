from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtWidgets import QDialog, QFrame, QLabel, QPushButton, QHBoxLayout
from PyQt5.uic import loadUi

from models import *

class List_Dialog(QDialog):
    def __init__(self, widget, orders_list, customer_name):
        """init function that set al the main stuff of th page like UI and clicked event"""
        super(List_Dialog, self).__init__()
        loadUi("UI/UI_Files/order_list_dialog.ui", self)  # load the UI of the page
        self.widget = widget  # the widget-stack that has all widgets --> so I can move to any other widget

        self.list_titel.setText(f"Orders for {customer_name.strip()}")

        self.orders = orders_list  # save orders list in object variable
        self.setup_order_in_list(len(orders_list))  # show the relevant frames

    def setup_order_in_list(self, count):
        for i in range(count):
            start_date, end_date = get_start_and_end_dates(order_id=self.orders[i][0])
            order_guest = str(self.orders[i][2]) + " Guests"
            self.user_orders_widget.addWidget(
                self.create_order_fream(order_id=self.orders[i][0], start_date=start_date, end_date=end_date,
                                        order_guests=order_guest))
            # self.frames[i][1].setText(str(get_start_and_end_dates(order_id=self.orders[i][0])))
            # self.frames[i][2].setText(str(self.orders[i][2]) + " Guests")

    def go_to_order(self, order_id=-1):
        self.widget.widget(windows_indexes["view-order"]).set_order_to_display(order_id=order_id)
        self.widget.widget(windows_indexes["view-order"]).display_order()
        self.widget.widget(windows_indexes["home-menu"]).search_order_line_edit.setText("")
        self.widget.setCurrentIndex(windows_indexes["view-order"])
        self.close()

    def create_order_fream(self, order_id=-1, start_date="", end_date="", order_guests=0):
        if order_id == -1 or start_date == "" or end_date == "" or order_guests == 0:
            return None

        order_frame = QFrame(self)
        order_frame.setProperty("listitem", "true")
        layout = QHBoxLayout(order_frame)
        layout.setContentsMargins(18, 10, 12, 10)
        layout.setSpacing(16)  # same columns as the titles frame in order_list_dialog.ui

        order_id_label = QLabel(order_frame)
        order_id_label.setObjectName("order_id")
        order_id_label.setFixedWidth(130)
        order_id_label.setProperty("role", "value")
        order_id_label.setText("#" + str(order_id).zfill(8))
        layout.addWidget(order_id_label)

        order_guests_label = QLabel(order_frame)
        order_guests_label.setObjectName("order_guests")
        order_guests_label.setFixedWidth(90)
        order_guests_label.setText(order_guests)
        layout.addWidget(order_guests_label)

        order_dates_label = QLabel(order_frame)
        order_dates_label.setObjectName("order_dates")
        order_dates_label.setText(f"{start_date}  →  {end_date}")
        layout.addWidget(order_dates_label, 1)

        order_view_btn = QPushButton(order_frame)
        order_view_btn.clicked.connect(lambda: self.go_to_order(order_id=order_id))
        order_view_btn.setObjectName("order_view_btn")
        order_view_btn.setText("Open")
        order_view_btn.setProperty("variant", "primary")
        order_view_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(order_view_btn)

        return order_frame
