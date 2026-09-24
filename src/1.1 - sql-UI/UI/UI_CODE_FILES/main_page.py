from PyQt5.QtCore import Qt, QDateTime, QSize, QTimer, QEvent
from PyQt5.QtWidgets import QMainWindow, QSizeGrip, QApplication, QDialog
from PyQt5.uic import loadUi

from models import *
from models import session
from UI import theme
from .title_bar import Title_Bar
from .home_menu_widget import Home_Menu_Widget
from .new_order_widget import New_Order_Widget
from .view_order_widget import View_Order_Widget
from .rooms_view_widget import Room_View_Widget
from .update_order_widget import Update_Order_Widget
from .settings_widget import Settings_Widget
from .orders_list_widget import Orders_List_Widget


# title + subtitle that the header shows for every page in the stack
PAGES_HEADERS = {
	windows_indexes["home-menu"]: ("Dashboard", "Search orders and jump to the daily work"),
	windows_indexes["new-order"]: ("New order", "Book a room for a guest"),
	windows_indexes["rooms-view"]: ("Rooms", "Live status of every room in the hotel"),
	windows_indexes["view-order"]: ("Order details", "Check guests in and out, update or delete the order"),
	windows_indexes["update-order"]: ("Update order", "Change the details of an existing order"),
	windows_indexes["settings"]: ("Settings", "Your account"),
	windows_indexes["orders"]: ("Orders", "Every order in the hotel"),
}

AUTO_LOCK_MINUTES = 15  # return to the login screen after this many minutes with no mouse/keyboard activity

# which sidebar button is marked for every page (order pages belong to "Orders")
PAGES_NAV = {
	windows_indexes["home-menu"]: "home",
	windows_indexes["orders"]: "orders",
	windows_indexes["new-order"]: "orders",
	windows_indexes["view-order"]: "orders",
	windows_indexes["update-order"]: "orders",
	windows_indexes["rooms-view"]: "rooms",
	windows_indexes["settings"]: "settings",
}


class Main_Page(QMainWindow):
	def __init__(self):
		"""init function that set al the main stuff of th page like UI and clicked event"""
		super(Main_Page, self).__init__()
		loadUi("UI/UI_Files/main_page.ui", self)  # load the UI of the page
		self.setWindowFlag(Qt.FramelessWindowHint)# this will hide the title bar (the app has its own header)
		self.setWindowTitle("Room Manager")
		self.want_relogin = False  # set to "logout"/"auto_lock" by relogin(); main.py checks this after the window closes
		######################## add title widget ########################
		self.title_bar=Title_Bar(self)
		self.top_widget.addWidget(self.title_bar)
		##################################################################


		######################## buttons section #########################
		self.setting_button.clicked.connect(self.settings_function)  # click event to the settings button
		self.nav_home_btn.clicked.connect(lambda: self.go_to_page(windows_indexes["home-menu"]))
		self.nav_orders_btn.clicked.connect(lambda: self.go_to_page(windows_indexes["orders"]))
		self.nav_rooms_btn.clicked.connect(lambda: self.go_to_page(windows_indexes["rooms-view"]))
		self.add_room_btn.clicked.connect(self.add_room_function)  # click event to the add room button
		self.nav_buttons = {
			"home": self.nav_home_btn,
			"orders": self.nav_orders_btn,
			"rooms": self.nav_rooms_btn,
			"settings": self.setting_button,
		}
		self.setup_sidebar_icons()
		self.apply_role_visibility()  # hide manager-only sidebar actions from a desk worker
		##################################################################


		####################### add widgets section ######################
		main_menu_widget=Home_Menu_Widget(self.widget_section)#create a home menu widget
		self.widget_section.insertWidget(windows_indexes["home-menu"], main_menu_widget)#add home menu widget to the stack
		#--------------------------------------------------------------------------------------------------------------#
		new_order_widget=New_Order_Widget(self.widget_section)  # create a new order widget
		self.widget_section.insertWidget(windows_indexes["new-order"], new_order_widget)  # add new order widget to the stack
		# -------------------------------------------------------------------------------------------------------------#
		rooms_view_widget = Room_View_Widget(self.widget_section)  # create a new order widget
		self.widget_section.insertWidget(windows_indexes [ "rooms-view" ],rooms_view_widget)  # add new order widget to the stack
		# -------------------------------------------------------------------------------------------------------------#
		view_order_widget = View_Order_Widget(self.widget_section)  # create a new order widget
		self.widget_section.insertWidget(windows_indexes [ "view-order" ],view_order_widget)  # add new order widget to the stack
		# -------------------------------------------------------------------------------------------------------------#
		update_order_widget = Update_Order_Widget(self.widget_section)  # create a new order widget
		self.widget_section.insertWidget(windows_indexes [ "update-order" ],update_order_widget)  # add new order widget to the stack
		# -------------------------------------------------------------------------------------------------------------#
		settings_widget = Settings_Widget(self.widget_section)  # create a settings widget
		self.widget_section.insertWidget(windows_indexes["settings"], settings_widget)  # add settings widget to the stack
		# -------------------------------------------------------------------------------------------------------------#
		orders_list_widget = Orders_List_Widget(self.widget_section)  # create a orders list widget
		self.widget_section.insertWidget(windows_indexes["orders"], orders_list_widget)  # add orders list widget to the stack
		# -------------------------------------------------------------------------------------------------------------#

		##################################################################
		self.widget_section.currentChanged.connect(self.page_changed)  # keep the header + sidebar in sync with the page
		self.widget_section.setCurrentIndex(windows_indexes["home-menu"])##start the program with the home menu widget##
		self.page_changed(windows_indexes["home-menu"])

		self.size_grip = QSizeGrip(self)  # the window has no system frame, so give it a resize handle
		self.content_layout.addWidget(self.size_grip, 0, Qt.AlignBottom | Qt.AlignRight)

		# the clock: a timer on the UI thread (a QThread with an endless loop could never be stopped, and every
		# log out / log in made a new Main_Page with one more of them running)
		self.clock_timer = QTimer(self)
		self.clock_timer.timeout.connect(self.set_time_and_date_for_display)
		self.clock_timer.start(1000)
		self.set_time_and_date_for_display()

		############### auto-lock: back to the login screen after AUTO_LOCK_MINUTES idle ###############
		self.idle_timer = QTimer(self)
		self.idle_timer.setInterval(AUTO_LOCK_MINUTES * 60 * 1000)
		self.idle_timer.timeout.connect(self.lock_now)
		self.idle_timer.start()
		QApplication.instance().installEventFilter(self)  # any click/key/scroll resets the idle timer


	def setup_sidebar_icons(self):
		sidebar_icons = [(self.nav_home_btn, "home"), (self.nav_orders_btn, "calendar"), (self.nav_rooms_btn, "bed"),
						 (self.add_room_btn, "plus"), (self.setting_button, "settings")]
		for btn, icon_name in sidebar_icons:
			btn.setIcon(theme.icon(icon_name, theme.COLORS["sidebar_text"], 20))
			btn.setIconSize(QSize(20, 20))


	def go_to_page(self, index):
		# start when click on one of the sidebar buttons
		if index == windows_indexes["rooms-view"]:
			self.widget_section.widget(index).set_filter("all")  # from the sidebar -> show all the rooms
		self.widget_section.setCurrentIndex(index)


	def add_room_function(self):
		# start when click on the add room button, show the rooms page if a room was added
		rooms_view_widget = self.widget_section.widget(windows_indexes["rooms-view"])
		if rooms_view_widget.new_room():
			self.go_to_page(windows_indexes["rooms-view"])


	def page_changed(self, index):
		title, subtitle = PAGES_HEADERS.get(index, ("", ""))
		self.title_bar.set_page_title(title, subtitle)
		for nav_name, btn in self.nav_buttons.items():
			theme.set_selected(btn, PAGES_NAV.get(index) == nav_name)


	def settings_function(self):
		# start when click on the settings button
		self.go_to_page(windows_indexes["settings"])


	def set_time_and_date_for_display(self):
		now = QDateTime.currentDateTime()
		self.time_and_date_label.setText(now.toString("hh:mm:ss"))
		self.date_label.setText(now.toString("ddd, dd MMM yyyy"))


	def apply_role_visibility(self):
		# a desk worker doesn't see manager-only sidebar actions (the DB layer refuses them too either way)
		self.add_room_btn.setVisible(session.current.is_manager())


	def relogin(self, reason="logout"):
		# close this window and tell main.py's loop to show the login screen again (used by Log out and auto-lock)
		self.want_relogin = reason
		self.close()


	def lock_now(self):
		# the app was idle for too long -> close any open dialog (as if "No"/"Cancel" was clicked), then go back to
		# the login screen. Without closing them, a dialog would stay open on top of the login screen.
		for _ in range(10):  # dialogs can be nested; the limit is only a guard against a dialog that refuses to close
			dialog = QApplication.activeModalWidget()
			if dialog is None:
				break
			dialog.reject() if isinstance(dialog, QDialog) else dialog.close()
		self.relogin(reason="auto_lock")


	def eventFilter(self, watched, event):
		if event.type() in (QEvent.MouseButtonPress, QEvent.KeyPress, QEvent.Wheel):
			self.idle_timer.start()  # any activity resets the idle countdown
		return super(Main_Page, self).eventFilter(watched, event)


	def closeEvent(self, event):
		QApplication.instance().removeEventFilter(self)  # this Main_Page is about to be destroyed
		self.idle_timer.stop()
		self.clock_timer.stop()
		super(Main_Page, self).closeEvent(event)
