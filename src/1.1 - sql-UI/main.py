import random, sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QDialog

from models import *
from  models.app_function import create_DB
from models import session
from models.dialogs.login_dialog import Login_Dialog
from UI.UI_CODE_FILES import Main_Page
from UI.theme import apply_theme


# self.time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def main():
	create_DB()
	app = QApplication(sys.argv)  # create the app
	apply_theme(app)  # colors, fonts and the global stylesheet of the app

	while True:
		session.current.logout()  # start every login attempt with a clean session
		login_dialog = Login_Dialog()
		if login_dialog.exec_() != QDialog.Accepted:
			break  # the login window was closed -> quit the app

		main_page = Main_Page()  # create main page
		main_page.show()
		app.exec_()
		if not main_page.want_relogin:
			break  # the window was closed (not "Log out" / auto-lock) -> quit the app
		# want_relogin -> loop back to the login screen without touching the DB connection

if __name__ == '__main__':
	main()
