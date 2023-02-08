from datetime import *

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QDate
from PyQt5.uic import loadUi

from models import *
from models.range_of_dates import Dates_Range


class New_Order_Widget(QWidget):
	def __init__(self, widget):
		"""init function that set al the main stuff of th page like UI and clicked event"""
		super(New_Order_Widget, self).__init__()
		loadUi("UI/UI_Files/new_order_widget.ui", self)  # load the UI of the page
		self.widget = widget  # the widget-stack that has all widgets --> so I can move to any other widget
		
		###############################self values##############################
		self.electric_car_status = False  # tell if the customer has electric car
		self.pet_status = False  # tell if the customer has a pet
		self.breakfast_status = False  # tell if the customer want breakfast
		self.lunch_status = False  # tell if the customer want lunch
		self.dinner_status = False  # tell if the customer want dinner
		#######################################################################
		
		##########################clicked events ##############################
		self.create_btn.clicked.connect(self.create_order)  # click event to the create order button
		self.check_electric_car_btn.clicked.connect(self.electric_car)
		self.check_pet_btn.clicked.connect(self.pet)
		self.breakfast_btn.clicked.connect(self.breakfast)
		self.lunch_btn.clicked.connect(self.lunch)
		self.dinner_btn.clicked.connect(self.dinner)
		######################################################################
		
		self.arrival_date.calendarWidget().clicked.connect(self.set_leaving_date_min)  # when select date for arrival
		self.arrival_date.setMinimumDate(QDate.currentDate().addDays(1))  # set the arrival minimum date to tomorrow
		self.leaving_date.setMinimumDate(
			QDate.currentDate().addDays(2))  # set the leaving minimum date to the day after tomorrow
	
	def set_leaving_date_min(self):
		day_after_arrival_date = self.arrival_date.date().addDays(2)  # the day after the date that select to arrival
		self.leaving_date.setMinimumDate(
			day_after_arrival_date)  # set minimum date fo leaving to be day after the day that select for arrival
	
	def create_order(self):
		"""
		Send all data from the front to the function that create order and add to database
		"""
		# print("-------------start create-----------")
		current_time = datetime.now().strftime("%H:%M:%S , %d/%m/%Y")
		customer_name = self.customer_name_input.text()
		guests = int(self.adults_input.text()) + int(self.kids_input.text())
		meal_options = str(int(self.breakfast_status)) + str(int(self.lunch_status)) + str(int(self.dinner_status))
		electric_car = self.electric_car_status
		pet = self.pet_status
		arrival = str(self.arrival_date.date().toPyDate().strftime("%d/%m/%Y"))
		leaving = str(self.leaving_date.date().toPyDate().strftime("%d/%m/%Y"))
		orders_create_status = add_new_order(customer_name, guests, meal_options, electric_car, pet, arrival, leaving)
		if orders_create_status == OK_CODE:
			self.widget.setCurrentIndex(windows_indexes [ "home-menu" ]) #return to home menu
		# print(f"created: {current_time}\n"
		#       f"name: {customer_name}\n"
		#       f"guests: {guests}\n"
		#       f"meals: {meal_options}\n"
		#       f"car: {electric_car}\n"
		#       f"pet: {pet}\n"
		#       f"arrival: {arrival}\n"
		#       f"leaving: {leaving}\n")
		# print("-------------end create------------")
		
	
	def breakfast(self):
		self.breakfast_status = not self.breakfast_status  # change status for the select
		style = """
			QPushButton:hover {
				background-color: rgb(48, 120, 200);
			}
			QPushButton{
				border-radius:15px;
				font: 25px "Calibri";
				border:1px solid rgb(255, 255, 255);
		"""  # the basic style for the button
		if self.breakfast_status:
			style += """background-color: rgb(48, 120, 200);"""  # add background color when the status is true
		style += """	}	"""  # close style
		self.breakfast_btn.setStyleSheet(style)  # set the style sheet for the button
	
	def lunch(self):
		self.lunch_status = not self.lunch_status  # change status for the select
		style = """
			QPushButton:hover {
				background-color: rgb(48, 120, 200);
			}
			QPushButton{
				border-radius:15px;
				font: 25px "Calibri";
				border:1px solid rgb(255, 255, 255);
		"""  # the basic style for the button
		if self.lunch_status:
			style += """background-color: rgb(48, 120, 200);"""  # add background color when the status is true
		style += """	}	"""  # close style
		self.lunch_btn.setStyleSheet(style)  # set the style sheet for the button
	
	def dinner(self):
		self.dinner_status = not self.dinner_status  # change status for the select
		style = """
			QPushButton:hover {
				background-color: rgb(48, 120, 200);
			}
			QPushButton{
				border-radius:15px;
				font: 25px "Calibri";
				border:1px solid rgb(255, 255, 255);
		"""  # the basic style for the button
		if self.dinner_status:
			style += """background-color: rgb(48, 120, 200);"""  # add background color when the status is true
		style += """	}	"""  # close style
		self.dinner_btn.setStyleSheet(style)  # set the style sheet for the button
	
	def electric_car(self):
		self.electric_car_status = not self.electric_car_status  # change status for the select
		style = """
			QPushButton:hover {
				background-color: rgb(10, 123, 204);
			}
			QPushButton{
				border-radius:15px;
				border-radius:10px;
				color: rgb(255, 255, 255);
				border:2px solid  rgb(255, 255, 255);	
		"""  # the basic style for the button
		if self.electric_car_status:
			style += """	background: rgb(10, 123, 204);	"""  # add background color when the status is true
		style += """	}	"""  # close style
		self.check_electric_car_btn.setStyleSheet(style)  # set the style sheet for the button
	
	def pet(self):
		self.pet_status = not self.pet_status  # change status for the select
		style = """
			QPushButton:hover {
				background-color: rgb(10, 123, 204);
			}
			QPushButton{
				border-radius:15px;
				border-radius:10px;
				color: rgb(255, 255, 255);
				border:2px solid  rgb(255, 255, 255);
		"""  # the basic style for the button
		if self.pet_status:
			style += """	background: rgb(10, 123, 204);	"""  # add background color when the status is true
		style += """	}	"""  # close style
		self.check_pet_btn.setStyleSheet(style)  # set the style sheet for the button
