from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi

from models import *


class New_Fault_Dialog(QDialog):
	def __init__(self):
		"""init function that set al the main stuff of th page like UI and clicked event"""
		super(New_Fault_Dialog, self).__init__()
		loadUi("UI/UI_Files/new_room_fault_dialog.ui", self)  # load the UI of the page

		
		self.add_fault_btn.clicked.connect(self.add_fault)
		self.cencel_btn.clicked.connect(self.cencel_btn_click)
		
		self.room_number=0  # stay 0 if the dialog is canceled
		self.fault=""

		self.load_rooms()


	def load_rooms(self):
		"""Fill the rooms list with the rooms that exist, so the user can't pick a room that doesn't exist"""
		try:
			rooms = get_rooms_from_db()
		except Exception as e:
			print(e)
			rooms = []
		for room in sorted(rooms, key=lambda r: r[0]):
			# room = (room_number, room_capacity, room_is_catch, room_is_clean, room_name)
			self.room_number_input.addItem(f"{room_display_name(room[0], room[4])}  ·  {room[1]} guests", room[0])
		if len(rooms) == 0:
			self.room_number_input.addItem("No rooms in the hotel yet")
			self.room_number_input.setEnabled(False)
			self.add_fault_btn.setEnabled(False)


	def add_fault(self):
		fault = self.fault_text_edit.toPlainText().strip()
		if fault == "":
			self.error_label.setText("Please describe the fault")
			return
		self.room_number = self.room_number_input.currentData()
		self.fault = fault
		self.close()
	def cencel_btn_click(self):
		self.close()
