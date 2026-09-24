import re
from datetime import datetime
from .global_ver import *
def create_range(start, end, order_id=0):
	# print(start, end, order_id)
	date_range=Dates_Range(start, end, order_id)
	if not date_range.range_ok:
		return ERROR_CODE
	return date_range
class Dates_Range():
	def __init__(self, start, end, order_id=-1):
		self.start=self.is_date(start)
		self.end=self.is_date(end)
		self.range_ok=False
		self.error_text=""
		self.order_id=order_id
		if self.start == "" or self.end == "":
			# if the function that check the date return empty string it means that one of the dates is not a date
			self.range_ok=False
			self.error_text="One of the dates is not good"
			return
		self.range_ok, self.error_text=self.check_range(start, end)
	def is_date(self, string):
		date=string
		regex=r'[\d]{1,2}/[\d]{1,2}/[\d]{4}'  # date format
		if re.fullmatch(regex, date) != None:  # check the string is in date format
			check_date_numbers=self.convert_to_int(date.split("/"))
			if (check_date_numbers[0] > 31 or check_date_numbers[0] < 1) or (
					check_date_numbers[1] > 12 or check_date_numbers[1] < 1):
				# check the day number is between 1 and 31 and the month number is between 1 and 12
				return ""
			try:
				datetime.strptime(date, "%d/%m/%Y")  # a real calendar date (no 31/02)
			except ValueError:
				return ""
			return date
		return ""

	def convert_to_int(self, list_to_convert):
		new_list=[]
		for i in list_to_convert:
			try:
				new_list.append(int(i))
			except:
				print("----ERROR: can not convert to int-----")
		return new_list

	def check_range(self, start, end):
		arrival=self.convert_to_int(start.split("/"))  # convert to list with number not strings
		leaving=self.convert_to_int(end.split("/"))  # convert to list with number not strings
		# 30/10/2020
		# 1/11/2020
		if arrival[2] == leaving[2]:
			# check range in the same year
			count=leaving[1]-arrival[1]
			if count > 2:
				# the range can be more than 2 month
				return False, "More then 2 month"
			if arrival[1] == leaving[1]:
				if arrival[0] == leaving[0]:
					# the arrival and leaving date are the same
					return False, "The same date"
				elif arrival[0] < leaving[0]:
					return True, ""
				elif arrival[0] > leaving[0]:
					# the days are inconsistent
					return False, "Day of arrival is after day of leaving"
			elif arrival[1] < leaving[1]:
				return True, ""
			elif arrival[1] > leaving[1]:
				# the months are inconsistent
				return False, "Month of arrival is after month of leaving"
		elif arrival[2] < leaving[2]:
			# check range when the year is different
			year_count=leaving[2]-arrival[2]
			month_count=(12-arrival[1])+leaving[1]
			# the range can be more than 2 month and certainly not more than two years
			if year_count > 1:
				return False, "More then a year"
			elif month_count > 2:
				return False, "More then 2 month"
			return True, ""
		elif arrival[2] > leaving[2]:
			# the years are inconsistent
			return False, "Year of arrival is after year of leaving"

	def set_order_id(self, order_id):
		self.order_id=order_id

	def get_order_id(self):
		return self.order_id

	def set_arrival_date(self, arrival_date):
		self.start=arrival_date
		return self.check_range(self.start,self.end)

	def get_arrival_date(self):
		return self.start

	def set_leaving_date(self, leaving_date):
		self.end=leaving_date
		return self.check_range(self.start, self.end)

	def get_leaving_date(self):
		return self.end

	def __str__(self, len1=10):
		title=str(str(str("---Range of dates---")).ljust(len1+10))+"||"
		start=str(str(str("Start: %s" % (self.start))).ljust(len1+10))+"||"
		end=str(str(str("End: %s" % (self.end))).ljust(len1+10))+"||"

		return (f"{title}\n"
		        f"{start}\n"
		        f"{end}")
