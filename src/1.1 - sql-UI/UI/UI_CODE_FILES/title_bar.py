from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QFrame
from PyQt5.uic import loadUi

from models import *
from models import session
from UI import theme

class Title_Bar(QFrame):
	def __init__(self, widget):
		"""init function that set al the main stuff of th page like UI and clicked event"""
		super(Title_Bar, self).__init__()
		loadUi("UI/UI_Files/title_bar.ui", self)  # load the UI of the page
		self.widget=widget  # the main window --> so I can close / minimize / move it
		self.drag_position = None

		role_label = "Manager" if session.current.is_manager() else "Desk"
		self.user_chip.setText(f"{session.current.display_name()}  ·  {role_label}")
		for btn, icon_name in [(self.minimize_button, "minimize"), (self.maximize_button, "maximize"),
							   (self.close_button, "close")]:
			btn.setIcon(theme.icon(icon_name, theme.COLORS["text_muted"], 18))
			btn.setIconSize(QSize(18, 18))
			btn.setCursor(Qt.PointingHandCursor)

		self.close_button.clicked.connect(self.close_app)
		self.minimize_button.clicked.connect(self.minimize_app)
		self.maximize_button.clicked.connect(self.maximize_app)


	def set_page_title(self, title, subtitle=""):
		self.page_title_label.setText(title)
		self.page_subtitle_label.setText(subtitle)


	def close_app(self):
		DB_CON.commit()
		DB_CURSER.close()
		DB_CON.close()
		self.widget.close()
	def minimize_app(self):
		self.widget.showMinimized()
	def maximize_app(self):
		if self.widget.isMaximized():
			self.widget.showNormal()
		else:
			self.widget.showMaximized()

	################ move the window by dragging the header ################
	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			self.drag_position = event.globalPos() - self.widget.frameGeometry().topLeft()
			event.accept()

	def mouseMoveEvent(self, event):
		if self.drag_position is not None and event.buttons() & Qt.LeftButton and not self.widget.isMaximized():
			self.widget.move(event.globalPos() - self.drag_position)
			event.accept()

	def mouseReleaseEvent(self, event):
		self.drag_position = None

	def mouseDoubleClickEvent(self, event):
		self.maximize_app()
