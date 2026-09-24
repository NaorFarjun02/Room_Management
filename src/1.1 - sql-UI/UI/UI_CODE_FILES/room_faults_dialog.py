
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QFrame, QLabel,QDialog, QHBoxLayout
from PyQt5.uic import loadUi

from models import *
from UI import theme


class Faults_Dialog(QDialog):
	def __init__(self, room_number,room_faults_list):
		"""init function that set al the main stuff of th page like UI and clicked event"""
		super(Faults_Dialog, self).__init__()
		loadUi("UI/UI_Files/room_faults_dialog.ui", self)  # load the UI of the page



		self.room_number_label.setText(str(room_number))

		for f in room_faults_list:
			self.faults_widget.addWidget(self.create_fault_frame(f[0]))




	def create_fault_frame(self,fault):
		faults_frame = QFrame(self)
		faults_frame.setObjectName(u"faults_frame")
		faults_frame.setProperty("listitem", "true")
		layout = QHBoxLayout(faults_frame)
		layout.setContentsMargins(16, 12, 16, 12)
		layout.setSpacing(12)

		fault_icon = QLabel(faults_frame)
		fault_icon.setPixmap(theme.pixmap("alert", theme.COLORS["warning"], 20))
		layout.addWidget(fault_icon, 0, Qt.AlignTop)

		start_date_label = QLabel(faults_frame)
		start_date_label.setObjectName(u"fault_label")
		start_date_label.setText(fault)
		start_date_label.setWordWrap(True)
		layout.addWidget(start_date_label, 1)

		return faults_frame
