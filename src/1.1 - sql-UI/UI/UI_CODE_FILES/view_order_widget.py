from PyQt5.QtWidgets import QApplication, QDialog, QDesktopWidget, QWidget
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.uic import loadUi

from models import *
from models.dialogs.dialog_msg import MSG_Dialog
from PyQt5.QtCore import QSize
from UI import theme

class View_Order_Widget(QWidget):
    def __init__(self, widget):
        """init function that set al the main stuff of th page like UI and clicked event"""
        super(View_Order_Widget, self).__init__()
        loadUi("UI/UI_Files/view_order_widget.ui", self)  # load the UI of the page
        self.widget = widget  # the widget-stack that has all widgets --> so I can move to any other widget
        self.order_id = None

        self.check_in_status = False
        self.check_out_status = False

        self.check_in_btn.clicked.connect(self.check_in_order)
        self.check_out_btn.clicked.connect(self.check_out_order)
        self.delete_btn.clicked.connect(self.delete_order)
        self.update_btn.clicked.connect(self.update_order)
        self.home_btn.clicked.connect(self.home)

        buttons_icons = [(self.check_in_btn, "check_in", theme.COLORS["accent"]),
                         (self.check_out_btn, "check_out", theme.COLORS["accent"]),
                         (self.update_btn, "edit", "#FFFFFF"),
                         (self.delete_btn, "trash", theme.COLORS["danger"]),
                         (self.home_btn, "arrow_left", theme.COLORS["text_muted"])]
        for btn, icon_name, color in buttons_icons:
            btn.setIcon(theme.icon(icon_name, color, 18))
            btn.setIconSize(QSize(18, 18))

        self.leaving_date = ""  # leaving date of the order that is displayed (dd/mm/yyyy)
        self.overdue_icon.setPixmap(theme.pixmap("alert", theme.COLORS["danger"], 20))
        self.overdue_banner.setVisible(False)  # shown only when the order is overdue

    def check_in_order(self):
        """
        Change the status of check-in for the order after ask the user in dialog
        """
        msg_label = "Check-in customer??" if not self.check_in_status else "Cancel check-in customer??"
        q = MSG_Dialog(msg_label, "Yes", "No")  # ask the user he want to check-in/undo the check-in for this order
        q.exec_()
        if q.status == "No":
            return
        self.check_in_status = not self.check_in_status  # change the status of check-in in the UI variable
        try:
            if self.check_in_status:
                # if the check-in status is True that mean the user is click to check-in the order
                error = check_in_db(order_id=self.order_id)  # tupel of (check-in status,error[,open order in the room])
                if error[0]:
                    # if no error check-in the customer
                    self.change_btn_color(self.check_in_btn, self.check_in_status)  # add color to button
                else:
                    # if there is a error when try to check-in
                    self.check_in_status = not self.check_in_status  # return the value to what was before the function
                    if len(error) > 2:
                        # another order is still open in the room -> let the user go to it
                        go_to = MSG_Dialog(error[1], "Open that order", "Cancel")
                        go_to.exec_()
                        if go_to.status == "Open that order":
                            self.set_order_to_display(error[2])
                            self.display_order()
                    else:
                        MSG_Popup(error[1]).exec_()  # show the error in popup msg
            # print(error[1])
            else:
                # if the check-in status is False that mean the user is click to cencel check-in the order
                if cancel_check_in_db(order_id=self.order_id)[0] == OK_CODE:
                    self.change_btn_color(self.check_in_btn, self.check_in_status)  # cencel the color of the button
                else:
                    # if the user is already check-out
                    self.check_in_status = not self.check_in_status  # return the value to what was before the function
                    MSG_Popup("The customer is already check out!!").exec_()
        # print("The customer is already check out!!")
        except Exception as e:
            print("check-in in widget", e)

    def check_out_order(self):
        """
        Change the status of check-out for the order after ask the user in dialog
        """
        msg_label = "Check-out customer and close order??" if not self.check_out_status else "Cancel check-out customer??"
        if not self.check_out_status and self.is_overdue():
            msg_label = f"The leaving date {self.leaving_date} has passed. Check-out the customer and close the order?"
        q = MSG_Dialog(msg_label, "Yes", "No")  # ask the user if he want to check-out/undo check-out for this order
        q.exec_()
        if q.status == "No":
            return
        self.check_out_status = not self.check_out_status  # change the status of check-out in the UI variable
        try:
            if self.check_out_status:
                # if the check-out status is True that mean the user is click to check-out the order
                error = check_out_db(order_id=self.order_id)  # tupel of (check-out status,error)
                if error[0]:
                    # if no error check-in the customer
                    self.change_btn_color(self.check_out_btn, self.check_out_status)  # add color to button
                    self.home()
                else:
                    # if there is a error when try to check-out
                    self.check_out_status = not self.check_out_status  # return the value to what was before the function
                    MSG_Popup(error[1]).exec_()  # show the error in popup msg
            # print(error[1])
            else:
                # if the check-out status is False that mean the user is click to cencel check-out the order
                cancel_check_out_db(order_id=self.order_id)
                self.change_btn_color(self.check_out_btn, self.check_out_status)  # cencel the color of the button

        except Exception as e:
            print("check-out in widget", e)

    def change_btn_color(self, btn, status):
        """
        Change the color of the button depend on his status (click/unclick)
        """
        theme.set_selected(btn, status)  # selected look when the status is true

    def delete_order(self):
        """
        Remove the order from the ORDERS list and go back to home page
        """
        delete_status = MSG_Dialog("Delete the order", "Yes", "No")
        delete_status.exec_()
        if delete_status.status == "No":
            return
        delete_status = delete_order_from_db_by_id(delete_code=DELETE_CODE, order_id=self.order_id)
        if delete_status[0] == ERROR_CODE:
            MSG_Popup(delete_status[1]).exec_()
            return
        MSG_Popup(delete_status[1]).exec_()
        self.home()

    def update_order(self):
        self.clear_ui()
        self.widget.widget(windows_indexes["update-order"]).set_order_id(self.order_id)
        self.widget.setCurrentIndex(windows_indexes["update-order"])  # return to home menu

    def home(self):
        """
        Go back to home page after clear the page from the current order that display
        """
        self.clear_ui()
        self.widget.setCurrentIndex(windows_indexes["home-menu"])  # return to home menu

    def clear_ui(self):
        """
        Clear the UI object -> set the text to defualt
        """
        self.order_id_label.setText("Order")
        self.overdue_banner.setVisible(False)
        self.created_by_label.setText("Order created by:")
        self.creation_date_label.setText("Order creation date: ")
        self.customer_name_label.setText("")
        self.adults_label.setValue(0)
        self.arrivel_label.setText("")
        self.leaving_label.setText("")
        order_widget_labels = [self.electric_car_label,
                               self.pet_label,
                               self.breakfast_label,
                               self.lunch_label,
                               self.dinner_label]
        for label in order_widget_labels:
            label.setPixmap(theme.status_pixmap(False))

    def display_order(self):
        """
        Put the data from the order in the UI objects
        """
        order = get_order_from_db_by_id(self.order_id)[1]
        orders_dates = get_start_and_end_dates(self.order_id)
        print(order)
        print(orders_dates)
        self.order_id_label.setText(f"Order #{str(order[0]).zfill(8)}")
        self.created_by_label.setText(f"Order created by: {order[12]}")
        self.creation_date_label.setText(f"Order creation date: {order[11]}")
        self.customer_name_label.setText(f"{order[1]}")
        self.adults_label.setValue(order[2])
        self.arrivel_label.setText(f"{orders_dates[0]}")
        self.leaving_label.setText(f"{orders_dates[1]}")
        order_vars_and_widget_labels = [(order[7], self.electric_car_label),
                                        (order[8], self.pet_label),
                                        (order[4], self.breakfast_label),
                                        (order[5], self.lunch_label),
                                        (order[6], self.dinner_label)]
        for order_stat in order_vars_and_widget_labels:
            order_stat[1].setPixmap(theme.status_pixmap(order_stat[0] == True))  # green check / grey dash

        # check-in / check-out buttons show the real status of the order
        self.check_in_status, self.check_out_status = order[9], order[10]
        self.change_btn_color(self.check_in_btn, self.check_in_status)
        self.change_btn_color(self.check_out_btn, self.check_out_status)

        # warning when the leaving date passed and the order is still open
        self.leaving_date = orders_dates[1]
        self.overdue_banner.setVisible(self.is_overdue())
        self.overdue_label.setText(f"The leaving date {self.leaving_date} has passed and the guest was not checked-out yet. "
                                   f"Check-out the guest to close the order and free room {order[3]}.")

    def is_overdue(self):
        return is_order_overdue(self.leaving_date, self.check_in_status, self.check_out_status)

    def set_order_to_display(self, order_id=-1):
        """
        Function that set the order variable for the widget

        :param order_to_display: The order you want to display
        :type order_to_display: Order
        """
        if order_id == -1:
            return ERROR_CODE, " Order ID can't be -1"
        self.order_id = order_id

# results = [t [ 1 ].setPixmap(QPixmap('UI/ICONS/checked.png')) if  t [ 0 ] == True else t [ 1 ].setPixmap(QPixmap('UI/ICONS/unchecked.png')) for t in order_vars_and_widget_labels]
