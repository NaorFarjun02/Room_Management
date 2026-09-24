"""Small reusable pieces of the new design that are built in code (not in .ui files)"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout

from UI import theme


def pill(text, tone="neutral", parent=None):
    """Rounded status label, tone = success / warning / danger / neutral / accent"""
    label = QLabel(text, parent)
    label.setProperty("tone", tone)
    label.setAlignment(Qt.AlignCenter)
    return label


def pill_holder(text, tone, width):
    """A pill inside a fixed width cell so it keeps its own size in a table row"""
    cell = QFrame()
    cell.setFixedWidth(width)
    layout = QHBoxLayout(cell)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(pill(text, tone), 0, Qt.AlignLeft | Qt.AlignVCenter)
    return cell


def cell(text, width=None, role=None):
    label = QLabel(str(text))
    if width:
        label.setFixedWidth(width)
    if role:
        label.setProperty("role", role)
    return label


class Stat_Tile(QFrame):
    """Card with a big number and a caption (used on the dashboard)"""

    def __init__(self, caption, icon_name, color):
        super(Stat_Tile, self).__init__()
        self.setProperty("card", "true")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        icon_label = QLabel()
        icon_label.setFixedSize(44, 44)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setPixmap(theme.pixmap(icon_name, color, 22))
        icon_label.setProperty("role", "card_icon")
        layout.addWidget(icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        self.value_label = QLabel("-")
        self.value_label.setProperty("role", "stat_value")
        caption_label = QLabel(caption)
        caption_label.setProperty("role", "stat_label")
        text_layout.addWidget(self.value_label)
        text_layout.addWidget(caption_label)
        layout.addLayout(text_layout)
        layout.addStretch()

    def set_value(self, value):
        self.value_label.setText(str(value))
