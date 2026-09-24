from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QFrame, QLabel,QDialog, QHBoxLayout, QPushButton
from PyQt5.uic import loadUi

from models import *
from models.dialogs.dialog_msg import MSG_Dialog
from UI import theme


class Faults_Dialog(QDialog):
	def __init__(self, room_number, room_faults_list, room_name=None):
		"""init function that set al the main stuff of th page like UI and clicked event"""
		super(Faults_Dialog, self).__init__()
		loadUi("UI/UI_Files/room_faults_dialog.ui", self)  # load the UI of the page

		self.room_number = room_number
		self.room_number_label.setText(room_display_name(room_number, room_name))

		for f in room_faults_list:
			self.faults_widget.addWidget(self.create_fault_frame(f[0]))




	def create_fault_frame(self,fault):
		faults_frame = QFrame(self)
		faults_frame.setObjectName(u"faults_frame")
		faults_frame.setProperty("listitem", "true")
		layout = QHBoxLayout(faults_frame)
		layout.setContentsMargins(16, 10, 10, 10)
		layout.setSpacing(12)

		fault_icon = QLabel(faults_frame)
		fault_icon.setPixmap(theme.pixmap("alert", theme.COLORS["warning"], 20))
		layout.addWidget(fault_icon, 0, Qt.AlignVCenter)

		start_date_label = QLabel(faults_frame)
		start_date_label.setObjectName(u"fault_label")
		start_date_label.setText(fault)
		start_date_label.setWordWrap(True)
		layout.addWidget(start_date_label, 1)

		fixed_btn = QPushButton(" Mark as fixed", faults_frame)
		fixed_btn.setObjectName(u"fault_fixed_btn")
		fixed_btn.setProperty("variant", "link")
		fixed_btn.setCursor(Qt.PointingHandCursor)
		fixed_btn.setIcon(theme.icon("check", theme.COLORS["accent"], 16))
		fixed_btn.setIconSize(QSize(16, 16))
		fixed_btn.clicked.connect(lambda: self.mark_fault_fixed(fault, faults_frame))
		layout.addWidget(fixed_btn, 0, Qt.AlignVCenter)

		return faults_frame


	def mark_fault_fixed(self, fault, fault_frame):
		"""Ask the user, then remove the fault from the room (and from the list)"""
		question = MSG_Dialog(f"Mark \"{fault}\" as fixed? It will be removed from the list", "Yes", "No")
		question.exec_()
		if question.status != "Yes":
			return
		delete_room_fault_db(self.room_number, fault)
		fault_frame.setParent(None)
		if self.faults_widget.count() == 0:  # no more faults in the room
			self.close()
