import random, sys
from PyQt5 import QtWidgets, sip
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

	relogin_reason = "logout"  # unused on the first pass (nobody is logged in yet, so logout() logs nothing)
	while True:
		session.current.logout(reason=relogin_reason)  # start every login attempt with a clean session
		login_dialog = Login_Dialog()
		if login_dialog.exec_() != QDialog.Accepted:
			break  # the login window was closed -> quit the app

		main_page = Main_Page()  # create main page
		main_page.show()
		app.exec_()
		relogin_reason = main_page.want_relogin  # "logout" or "auto_lock" -> logged by the logout() call above, next loop
		sip.delete(main_page)  # free the closed window now - the next login builds a new one
		if not relogin_reason:
			break  # the window was closed (not "Log out" / auto-lock) -> quit the app

if __name__ == '__main__':
	main()
