from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QFrame, QPushButton
from PyQt5.uic import loadUi

from models import *
from UI import theme
from .components import cell, pill_holder, table_header, table_row_layout

COLUMNS_TITLES = ["ORDER", "CUSTOMER", "GUESTS", "ROOM", "DATES", "STATUS"]
COLUMNS_WIDTH = [110, 180, 80, 150, 190, 130]  # ROOM is wider than just a number to fit a room's display name


class Orders_List_Widget(QWidget):
    """Page with all the orders, only the open ones (not checked-out) unless "Show closed orders" is on"""

    def __init__(self, widget):
        """init function that set al the main stuff of th page like UI and clicked event"""
        super(Orders_List_Widget, self).__init__()
        loadUi("UI/UI_Files/orders_list_widget.ui", self)  # load the UI of the page
        self.widget = widget  # the widget-stack that has all widgets --> so I can move to any other widget
        self.show_closed = False

        self.table_header_layout.addWidget(table_header(COLUMNS_TITLES, COLUMNS_WIDTH, trailing_width=90))
        self.new_order_btn.setIcon(theme.icon("plus", "#FFFFFF", 16))
        self.new_order_btn.setIconSize(QSize(16, 16))

        self.show_closed_btn.clicked.connect(self.toggle_show_closed)
        self.new_order_btn.clicked.connect(self.new_order)

    def showEvent(self, event):
        # every time the page is shown, load the orders again
        super(Orders_List_Widget, self).showEvent(event)
        self.refresh_orders()

    def toggle_show_closed(self):
        self.show_closed = not self.show_closed
        theme.set_selected(self.show_closed_btn, self.show_closed)
        self.refresh_orders()

    def new_order(self):
        self.widget.setCurrentIndex(windows_indexes["new-order"])

    def clear_orders_table(self):
        for i in reversed(range(self.orders_widget.count())):
            self.orders_widget.itemAt(i).widget().setParent(None)

    def refresh_orders(self):
        self.clear_orders_table()
        try:
            orders = get_all_orders_from_db(include_closed=self.show_closed)
        except Exception as e:
            print(e)
            return
        for order in orders:
            self.orders_widget.addWidget(self.create_order_frame(order))

        open_orders = sum(1 for o in orders if not o[5])
        self.title_label.setText("All orders" if self.show_closed else "Open orders")
        if self.show_closed:
            self.orders_count_label.setText(f"{len(orders)} orders  ·  {open_orders} open, {len(orders) - open_orders} closed")
        else:
            self.orders_count_label.setText(f"{len(orders)} open orders")

        if len(orders) == 0:
            empty_label = cell("No open orders - closed orders are hidden, use \"Show closed orders\" to see them"
                               if not self.show_closed else "No orders yet", role="muted")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setMinimumHeight(120)
            self.orders_widget.addWidget(empty_label)

    def create_order_frame(self, order):
        # order = (id, customer_name, number_of_guests, room_number, check_in, check_out, start_date, end_date, room_name)
        order_frame = QFrame(self)
        order_frame.setProperty("row", "true")
        order_frame.setFixedHeight(60)
        layout = table_row_layout(order_frame)

        layout.addWidget(cell("#" + str(order[0]).zfill(8), COLUMNS_WIDTH[0], "cell_strong"))
        layout.addWidget(cell(order[1], COLUMNS_WIDTH[1]))
        layout.addWidget(cell(order[2], COLUMNS_WIDTH[2]))
        layout.addWidget(cell(room_display_name(order[3], order[8]), COLUMNS_WIDTH[3]))
        dates = f"{order[6]}  →  {order[7]}" if order[6] else "-"
        layout.addWidget(cell(dates, COLUMNS_WIDTH[4]))
        if order[5]:
            layout.addWidget(pill_holder("Closed", "neutral", COLUMNS_WIDTH[5]))
        elif is_order_overdue(order[7], order[4], order[5]):
            layout.addWidget(pill_holder("Overdue", "danger", COLUMNS_WIDTH[5]))  # leaving date passed, not checked-out
        elif order[4]:
            layout.addWidget(pill_holder("Checked in", "info", COLUMNS_WIDTH[5]))
        else:
            layout.addWidget(pill_holder("Booked", "accent", COLUMNS_WIDTH[5]))
        layout.addStretch()

        open_btn = QPushButton("Open", order_frame)
        open_btn.setProperty("variant", "link")
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setIcon(theme.icon("arrow_right", theme.COLORS["accent"], 16))
        open_btn.setIconSize(QSize(16, 16))
        open_btn.setLayoutDirection(Qt.RightToLeft)  # the arrow after the text
        open_btn.clicked.connect(lambda: self.open_order(order[0]))
        layout.addWidget(open_btn)

        return order_frame

    def open_order(self, order_id):
        view_order_widget = self.widget.widget(windows_indexes["view-order"])
        view_order_widget.set_order_to_display(order_id)
        view_order_widget.display_order()
        self.widget.setCurrentIndex(windows_indexes["view-order"])
