from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi

from .list_dialog import List_Dialog
from models import *
from models.dialogs.popup_msg import MSG_Popup
from UI import theme
from .components import Stat_Tile


class Home_Menu_Widget(QWidget):
    def __init__(self, widget):
        """init function that set al the main stuff of th page like UI and clicked event"""
        super(Home_Menu_Widget, self).__init__()
        loadUi("UI/UI_Files/home_menu_widget.ui", self)  # load the UI of the page
        self.widget = widget  # the widget-stack that has all widgets --> so I can move to any other widget

        ############### buttons section #############
        self.new_order_button.clicked.connect(self.new_order_function)  # click event to the new order button
        self.rooms_button.clicked.connect(self.rooms_function)  # click event to the rooms button

        self.search_order_button.clicked.connect(self.search_order_function)  # click event to the search order button
        self.search_order_line_edit.returnPressed.connect(self.search_order_function)  # Enter in the search line = search

        ############### icons section ###############
        self.search_order_line_edit.addAction(theme.icon("search", theme.COLORS["text_faint"], 18),
                                              self.search_order_line_edit.LeadingPosition)
        self.rooms_card_icon.setPixmap(theme.pixmap("bed", theme.COLORS["accent"], 26))
        self.new_order_card_icon.setPixmap(theme.pixmap("calendar", theme.COLORS["accent"], 26))
        self.rooms_button.setIcon(theme.icon("arrow_right", theme.COLORS["text"], 16))
        self.new_order_button.setIcon(theme.icon("plus", "#FFFFFF", 16))
        for btn in (self.rooms_button, self.new_order_button):
            btn.setIconSize(QSize(16, 16))

        ############### rooms at a glance ###############
        self.stat_tiles = {
            "total": Stat_Tile("Rooms in the hotel", "bed", theme.COLORS["accent"]),
            "free": Stat_Tile("Available now", "check", theme.COLORS["success"]),
            "catch": Stat_Tile("Occupied now", "users", theme.COLORS["accent"]),
            "dirty": Stat_Tile("Need cleaning", "alert", theme.COLORS["warning"]),
        }
        tiles_filters = {"total": "all", "free": "free", "catch": "catch", "dirty": "dirty"}
        for key, tile in self.stat_tiles.items():
            self.stats_layout.addWidget(tile)
            tile.clicked.connect(lambda k=key: self.show_rooms_filtered(tiles_filters[k]))  # rooms page with the filter

    def showEvent(self, event):
        # every time the dashboard is shown, refresh the rooms numbers
        super(Home_Menu_Widget, self).showEvent(event)
        self.refresh_stats()

    def refresh_stats(self):
        try:
            rooms = get_rooms_status_from_db()  # (room_number, capacity, occupied_now, is_clean, faults_count)
        except Exception as e:
            print(e)
            return
        self.stat_tiles["total"].set_value(len(rooms))
        self.stat_tiles["catch"].set_value(sum(1 for r in rooms if r[2]))
        self.stat_tiles["free"].set_value(sum(1 for r in rooms if not r[2]))
        self.stat_tiles["dirty"].set_value(sum(1 for r in rooms if not r[3]))

    #############################################

    def new_order_function(self):
        # start when click on the new-order button
        self.widget.setCurrentIndex(windows_indexes["new-order"])

    def rooms_function(self):
        # start when click on the rooms button
        self.show_rooms_filtered("all")

    def show_rooms_filtered(self, filter_key):
        # go to the rooms page and show only the rooms in the filter (all / free / catch / dirty)
        self.widget.widget(windows_indexes["rooms-view"]).set_filter(filter_key)
        self.widget.setCurrentIndex(windows_indexes["rooms-view"])

    def search_order_function(self):
        # start when click on the search-order button
        text_to_search = self.search_order_line_edit.text()
        finds_orders = ()
        if text_to_search.isnumeric():
            finds_orders = get_order_from_db_by_id(
                order_id=text_to_search.zfill(8))  # if the user enter a number send if to the search function
            search_type = "NUMBER"
        elif text_to_search.isalpha():
            finds_orders = get_order_from_db_by_customer_name(
                customer_name=text_to_search)  # if the user enter a plain text send if to the search function
            search_type = "TEXT"
        else:
            MSG_Popup(
                "You need to enter name or order number to search").exec_()  # else, show popup msg telling the user that he need to enter text/number
            return "You need to enter name or order number to search"
        status_code,orders=finds_orders[0],finds_orders[1]

        if status_code == ERROR_CODE:
            text_to_msg = f"Can't find orders with the name:{text_to_search}" if search_type == "TEXT" else f"Can't find order number:{text_to_search}"
            MSG_Popup(text_to_msg).exec_()  # show poopup msg
            return text_to_msg
        elif status_code == MULTI_ORDERS:
            dialog_list = List_Dialog(self.widget, orders,
                                      text_to_search)  # create list dialog with the customer orders
            dialog_list.exec_()
        elif status_code == OK_CODE:
            self.widget.widget(windows_indexes["view-order"]).set_order_to_display(orders[0])
            self.widget.widget(windows_indexes[
                                   "view-order"]).display_order()  # run the function that put the data in the ui in view_order_widget
            self.search_order_line_edit.setText("")  # clear search line
            self.widget.setCurrentIndex(windows_indexes["view-order"])  # go to view order widget that display the order
