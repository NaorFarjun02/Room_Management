from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QFrame, QLabel,QDialog, QHBoxLayout
from PyQt5.uic import loadUi

from models import *
from UI import theme


class Dates_Catch_Dialog(QDialog):
	def __init__(self, room_number, room_dates_catch_list, room_name=None):
		"""init function that set al the main stuff of th page like UI and clicked event"""
		super(Dates_Catch_Dialog, self).__init__()
		loadUi("UI/UI_Files/room_dates_catch_dialog.ui", self)  # load the UI of the page



		self.room_number_label.setText(room_display_name(room_number, room_name))

		for d in room_dates_catch_list:
			self.dates_catch_widget.addWidget(self.create_date_frame(d))




	def create_date_frame(self,date):
		dates_frame = QFrame(self)
		dates_frame.setObjectName(u"dates_frame")
		dates_frame.setProperty("listitem", "true")
		layout = QHBoxLayout(dates_frame)
		layout.setContentsMargins(16, 12, 16, 12)
		layout.setSpacing(12)

		calendar_icon = QLabel(dates_frame)
		calendar_icon.setPixmap(theme.pixmap("calendar", theme.COLORS["accent"], 20))
		layout.addWidget(calendar_icon)

		start_date_label = QLabel(dates_frame)
		start_date_label.setObjectName(u"start_date_label")
		start_date_label.setText(date[0])
		start_date_label.setProperty("role", "value")
		layout.addWidget(start_date_label)

		to_label = QLabel(dates_frame)
		to_label.setObjectName(u"to_label")
		to_label.setPixmap(theme.pixmap("arrow_right", theme.COLORS["text_faint"], 16))
		layout.addWidget(to_label)

		end_date_label = QLabel(dates_frame)
		end_date_label.setObjectName(u"end_date_label")
		end_date_label.setText(date[1])
		end_date_label.setProperty("role", "value")
		layout.addWidget(end_date_label)
		layout.addStretch()

		return dates_frame
