"""
Central design system for the app: colors, fonts, the global Qt stylesheet and a small SVG icon set.

Every page gets its look from here (apply_theme is called once in main.py), so the .ui files
only describe layout and the widgets use objectName / dynamic properties ("variant", "selected", "tone")
to pick their style.
"""
from PyQt5.QtCore import Qt, QByteArray, QRectF
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QFont, QFontDatabase
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QStyleFactory

########################################## colors ##########################################
COLORS = {
    "bg": "#F4F6F8",  # app background
    "surface": "#FFFFFF",  # cards
    "surface_alt": "#F8FAFB",  # table header / inputs
    "border": "#E3E8EE",
    "border_strong": "#CBD3DC",
    "text": "#1F2937",
    "text_muted": "#6B7280",
    "text_faint": "#9AA3AF",

    "sidebar": "#16222E",
    "sidebar_hover": "#223242",
    "sidebar_active": "#2A3D50",
    "sidebar_text": "#C3CEDA",
    "sidebar_muted": "#6F8193",

    "accent": "#0F766E",  # primary actions
    "accent_hover": "#115E59",
    "accent_pressed": "#134E4A",
    "accent_soft": "#E0F2F0",
    "accent_soft_border": "#9ED7D0",
    "accent_light": "#5EEAD4",

    "success": "#067647",
    "success_soft": "#DCFAE6",
    "warning": "#B54708",
    "warning_soft": "#FEF0C7",
    "info": "#3538CD",
    "info_soft": "#E0EAFF",
    "danger": "#B42318",
    "danger_hover": "#912018",
    "danger_soft": "#FEE4E2",
}

FONT_FAMILIES = ["Segoe UI", "Inter", "Helvetica Neue", "Noto Sans", "DejaVu Sans", "Arial"]

########################################## icons ##########################################
# 24x24 line icons, stroke color is filled in when the icon is rendered
_ICON_PATHS = {
    "home": '<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "bed": '<path d="M2 20V5M2 16h20M22 20v-7a3 3 0 0 0-3-3h-8v6"/><circle cx="6.5" cy="12" r="2"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "alert": '<path d="M12 3.5 2.5 20h19z"/><path d="M12 10v4M12 17h.01"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "minimize": '<path d="M5 12h14"/>',
    "maximize": '<rect x="5" y="5" width="14" height="14" rx="2"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "settings": '<path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>',
    "trash": '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
    "edit": '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="m13.5 6.5 4 4"/>',
    "check_in": '<path d="M10 17l5-5-5-5M15 12H3M14 3h5a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-5"/>',
    "check_out": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14a6.5 6.5 0 0 1 3.5 6"/>',
    "bolt": '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    "paw": '<circle cx="5.5" cy="10" r="1.8"/><circle cx="9.5" cy="5.5" r="1.8"/><circle cx="14.5" cy="5.5" r="1.8"/>'
           '<circle cx="18.5" cy="10" r="1.8"/><path d="M12 11.5c-3 0-6 3.8-6 6.3C6 19.3 7.2 20.5 8.7 20.5c1.2 0 2.1-.7 3.3-.7s2.1.7 3.3.7c1.5 0 2.7-1.2 2.7-2.7 0-2.5-3-6.3-6-6.3z"/>',
    "coffee": '<path d="M4 9h13v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z"/><path d="M17 10.5h1.5a2.5 2.5 0 0 1 0 5H17M8 3v3M12 3v3"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "moon": '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
    "arrow_left": '<path d="M19 12H5M11 18l-6-6 6-6"/>',
    "arrow_right": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6v.3M12 17h.01"/>',
    "wrench": '<path d="M14.5 5.5a4 4 0 0 0 5 5L11 19a2.1 2.1 0 0 1-3-3l8.5-8.5a4 4 0 0 0-2-2z"/>',
}

# filled icons (not stroked) used as status markers
_FILLED_ICONS = {
    "status_on": '<circle cx="12" cy="12" r="10" fill="{color}"/>'
                 '<path d="M7.5 12.5l3 3 6-6.5" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>',
    "status_off": '<circle cx="12" cy="12" r="9" fill="none" stroke="{color}" stroke-width="2"/>'
                  '<path d="M8.5 12h7" stroke="{color}" stroke-width="2" stroke-linecap="round"/>',
}


def _svg(name, color):
    if name in _FILLED_ICONS:
        body = _FILLED_ICONS[name].format(color=color)
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">{body}</svg>'
    body = _ICON_PATHS[name]
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{body}</svg>')


def pixmap(name, color=None, size=20):
    """Render one of the icons above to a crisp (hi-dpi aware) pixmap"""
    color = color or COLORS["text"]
    scale = 2
    renderer = QSvgRenderer(QByteArray(_svg(name, color).encode()))
    image = QPixmap(size * scale, size * scale)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size * scale, size * scale))
    painter.end()
    image.setDevicePixelRatio(scale)
    return image


def icon(name, color=None, size=20):
    return QIcon(pixmap(name, color, size))


def status_pixmap(status, size=22):
    """Green check circle when status is true, grey dash circle when false"""
    if status:
        return pixmap("status_on", COLORS["success"], size)
    return pixmap("status_off", COLORS["text_faint"], size)


def set_selected(widget, status):
    """Toggle the 'selected' look of a chip / toggle button (see [selected="true"] in the stylesheet)"""
    widget.setProperty("selected", bool(status))
    repolish(widget)


def repolish(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


########################################## stylesheet ##########################################
_STYLESHEET = """
* {{
    color: {text};
    font-size: 14px;
    outline: none;
}}
QMainWindow, QDialog {{
    background: {bg};
}}
QWidget#app_root, QWidget#content_area, QStackedWidget#widget_section, QStackedWidget#widget_section > QWidget {{
    background: {bg};
}}
QToolTip {{
    background: {sidebar};
    color: #FFFFFF;
    border: none;
    padding: 6px 8px;
    border-radius: 6px;
}}

/* ------------------------------------------------ sidebar ------------------------------------------------ */
QFrame#sidebar {{
    background: {sidebar};
    border: none;
}}
QFrame#sidebar QLabel {{
    background: transparent;
    color: {sidebar_text};
}}
QFrame#sidebar QLabel#brand_mark {{
    background: {accent};
    color: #FFFFFF;
    border-radius: 12px;
    font-size: 16px;
    font-weight: 700;
}}
QFrame#sidebar QLabel#brand_title {{
    color: #FFFFFF;
    font-size: 17px;
    font-weight: 600;
}}
QFrame#sidebar QLabel#brand_subtitle, QFrame#sidebar QLabel#nav_section_label {{
    color: {sidebar_muted};
    font-size: 12px;
}}
QFrame#sidebar QLabel#nav_section_label {{
    font-weight: 600;
    letter-spacing: 1px;
    padding: 0 12px;
}}
QFrame#sidebar QPushButton {{
    background: transparent;
    color: {sidebar_text};
    border: none;
    border-radius: 10px;
    padding: 11px 14px;
    text-align: left;
    font-size: 14px;
}}
QFrame#sidebar QPushButton:hover {{
    background: {sidebar_hover};
    color: #FFFFFF;
}}
QFrame#sidebar QPushButton[selected="true"] {{
    background: {sidebar_active};
    color: #FFFFFF;
    font-weight: 600;
    border-left: 3px solid {accent_light};
    padding-left: 11px;
}}
QFrame#clock_card {{
    background: {sidebar_hover};
    border-radius: 12px;
}}
QFrame#sidebar QLabel#time_and_date_label {{
    color: #FFFFFF;
    font-size: 26px;
    font-weight: 600;
}}
QFrame#sidebar QLabel#date_label {{
    color: {sidebar_muted};
    font-size: 12px;
}}

/* ------------------------------------------------ header bar ------------------------------------------------ */
QFrame#title_bar {{
    background: {surface};
    border: none;
    border-bottom: 1px solid {border};
}}
QLabel#page_title_label {{
    font-size: 22px;
    font-weight: 600;
}}
QLabel#page_subtitle_label {{
    color: {text_muted};
    font-size: 13px;
}}
QLabel#user_chip {{
    background: {surface_alt};
    border: 1px solid {border};
    border-radius: 16px;
    padding: 6px 14px;
    color: {text_muted};
    font-size: 13px;
}}
QPushButton#minimize_button, QPushButton#maximize_button, QPushButton#close_button {{
    background: transparent;
    border: none;
    border-radius: 8px;
    min-width: 34px; max-width: 34px;
    min-height: 34px; max-height: 34px;
}}
QPushButton#minimize_button:hover, QPushButton#maximize_button:hover {{
    background: {surface_alt};
}}
QPushButton#close_button:hover {{
    background: {danger_soft};
}}

/* ------------------------------------------------ typography ------------------------------------------------ */
QLabel {{
    background: transparent;
}}
QLabel[role="h1"] {{
    font-size: 24px;
    font-weight: 600;
}}
QLabel[role="h2"] {{
    font-size: 16px;
    font-weight: 600;
}}
QLabel[role="muted"] {{
    color: {text_muted};
    font-size: 13px;
}}
QLabel[role="caption"] {{
    color: {text_muted};
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}
QLabel[role="value"] {{
    font-size: 16px;
    font-weight: 600;
}}
QLabel[role="error"] {{
    color: {danger};
    font-size: 13px;
    font-weight: 600;
}}

/* ------------------------------------------------ cards ------------------------------------------------ */
QFrame[card="true"] {{
    background: {surface};
    border: 1px solid {border};
    border-radius: 14px;
}}
QFrame[clickable="true"]:hover {{
    border: 1px solid {accent_soft_border};
    background: #FBFEFD;
}}
QFrame[card="true"] QFrame[card="inner"] {{
    background: {surface_alt};
    border: 1px solid {border};
    border-radius: 10px;
}}
QFrame#hero_frame {{
    border: none;
    border-radius: 18px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {sidebar}, stop:1 {accent_pressed});
}}
QFrame#hero_frame QLabel {{
    color: #FFFFFF;
}}
QFrame#hero_frame QLabel#title_label {{
    font-size: 30px;
    font-weight: 600;
}}
QFrame#hero_frame QLabel#hero_subtitle {{
    color: #B8CCD6;
    font-size: 15px;
}}
QFrame#hero_frame QLabel#search_hint {{
    color: #8FA9B8;
    font-size: 12px;
}}

/* ------------------------------------------------ buttons ------------------------------------------------ */
QPushButton {{
    background: {surface};
    border: 1px solid {border_strong};
    border-radius: 10px;
    padding: 9px 18px;
    font-size: 14px;
    font-weight: 600;
    color: {text};
}}
QPushButton:hover {{
    background: {surface_alt};
    border-color: {text_faint};
}}
QPushButton:pressed {{
    background: {border};
}}
QPushButton:disabled {{
    color: {text_faint};
    background: {surface_alt};
}}
QPushButton[variant="primary"] {{
    background: {accent};
    border: 1px solid {accent};
    color: #FFFFFF;
}}
QPushButton[variant="primary"]:hover {{
    background: {accent_hover};
    border-color: {accent_hover};
}}
QPushButton[variant="primary"]:pressed {{
    background: {accent_pressed};
}}
QPushButton[variant="danger"] {{
    background: {surface};
    border: 1px solid #F2B8B5;
    color: {danger};
}}
QPushButton[variant="danger"]:hover {{
    background: {danger_soft};
    border-color: {danger};
}}
QPushButton[variant="ghost"] {{
    background: transparent;
    border: 1px solid transparent;
    color: {text_muted};
}}
QPushButton[variant="ghost"]:hover {{
    background: {border};
    color: {text};
}}
QPushButton[variant="icon"] {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 0;
    min-width: 34px; max-width: 34px;
    min-height: 34px; max-height: 34px;
}}
QPushButton[variant="icon"]:hover {{
    background: {danger_soft};
}}
QPushButton[variant="link"] {{
    background: transparent;
    border: 1px solid {border};
    border-radius: 8px;
    padding: 6px 12px;
    color: {accent};
    font-size: 13px;
    text-align: left;
}}
QPushButton[variant="link"]:hover {{
    background: {accent_soft};
    border-color: {accent_soft_border};
}}
QPushButton[variant="hero"] {{
    background: {accent_light};
    border: none;
    color: {sidebar};
    padding: 12px 24px;
    font-size: 15px;
}}
QPushButton[variant="hero"]:hover {{
    background: #99F6E4;
}}
QPushButton[variant="tile"] {{
    background: {surface};
    border: 1px solid {border};
    border-radius: 16px;
    padding: 24px;
    text-align: left;
    font-size: 18px;
    font-weight: 600;
}}
QPushButton[variant="tile"]:hover {{
    border: 1px solid {accent_soft_border};
    background: #FBFEFD;
}}

/* chips = toggle buttons (meals / extras / check-in) */
QPushButton[variant="chip"] {{
    background: {surface};
    border: 1px solid {border_strong};
    border-radius: 10px;
    padding: 10px 16px;
    color: {text_muted};
    font-weight: 600;
}}
QPushButton[variant="chip"]:hover {{
    border-color: {accent};
    color: {text};
}}
QPushButton[variant="chip"][selected="true"] {{
    background: {accent_soft};
    border: 1px solid {accent};
    color: {accent_pressed};
}}

/* ------------------------------------------------ inputs ------------------------------------------------ */
QLineEdit, QSpinBox, QDateEdit, QTextEdit, QPlainTextEdit {{
    background: {surface};
    border: 1px solid {border_strong};
    border-radius: 10px;
    padding: 8px 12px;
    font-size: 15px;
    selection-background-color: {accent_soft_border};
    selection-color: {text};
}}
QLineEdit:focus, QSpinBox:focus, QDateEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 2px solid {accent};
    padding: 7px 11px;
}}
QSpinBox[readOnly="true"] {{
    background: transparent;
    border: none;
    padding: 0;
    font-size: 16px;
    font-weight: 600;
}}
QComboBox {{
    background: {surface};
    border: 1px solid {border_strong};
    border-radius: 10px;
    padding: 8px 12px;
    font-size: 15px;
}}
QComboBox:focus, QComboBox:on {{
    border: 2px solid {accent};
    padding: 7px 11px;
}}
QComboBox:disabled {{
    color: {text_faint};
    background: {surface_alt};
}}
QComboBox::drop-down {{
    subcontrol-origin: border;
    subcontrol-position: center right;
    width: 32px;
    border: none;
}}
QComboBox::down-arrow {{ image: url(UI/ICONS/theme/chevron_down.svg); width: 14px; height: 14px; }}
QComboBox QAbstractItemView {{
    background: {surface};
    border: 1px solid {border};
    padding: 4px;
    outline: none;
    selection-background-color: {accent_soft};
    selection-color: {accent_pressed};
}}
QFrame#hero_frame QLineEdit {{
    background: #FFFFFF;
    border: none;
    border-radius: 12px;
    padding: 12px 16px;
    font-size: 16px;
}}
QFrame#hero_frame QLineEdit:focus {{
    border: 2px solid {accent_light};
    padding: 10px 14px;
}}
QSpinBox {{
    padding-right: 26px;
}}
QSpinBox::up-button, QSpinBox::down-button {{
    subcontrol-origin: border;
    width: 26px;
    border: none;
    background: transparent;
}}
QSpinBox::up-button {{ subcontrol-position: top right; margin-top: 3px; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; margin-bottom: 3px; }}
QSpinBox::up-arrow {{ image: url(UI/ICONS/theme/chevron_up.svg); width: 12px; height: 12px; }}
QSpinBox::down-arrow {{ image: url(UI/ICONS/theme/chevron_down.svg); width: 12px; height: 12px; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: {surface_alt}; border-radius: 6px; }}
QDateEdit::drop-down {{
    subcontrol-origin: border;
    subcontrol-position: center right;
    width: 34px;
    border: none;
}}
QDateEdit::down-arrow {{ image: url(UI/ICONS/theme/calendar.svg); width: 18px; height: 18px; }}

/* calendar popup */
QCalendarWidget QWidget {{
    alternate-background-color: {surface_alt};
}}
QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background: {accent};
    min-height: 40px;
}}
QCalendarWidget QToolButton {{
    color: #FFFFFF;
    background: transparent;
    font-weight: 600;
    font-size: 14px;
    padding: 4px 8px;
    border-radius: 6px;
}}
QCalendarWidget QToolButton:hover {{
    background: {accent_hover};
}}
QCalendarWidget QAbstractItemView {{
    selection-background-color: {accent};
    selection-color: #FFFFFF;
    font-size: 13px;
}}
QCalendarWidget QAbstractItemView:disabled {{
    color: {text_faint};
}}

/* ------------------------------------------------ scroll areas / lists ------------------------------------------------ */
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: {border_strong};
    border-radius: 3px;
    min-height: 40px;
}}
QScrollBar::handle:vertical:hover {{
    background: {text_faint};
}}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{
    height: 0; background: none;
}}

QFrame#table_header {{
    background: {surface_alt};
    border: none;
    border-bottom: 1px solid {border};
    border-top-left-radius: 14px;
    border-top-right-radius: 14px;
}}
QFrame#table_header QLabel {{
    color: {text_muted};
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}
QFrame[row="true"] {{
    background: transparent;
    border: none;
    border-bottom: 1px solid {border};
}}
QFrame[row="true"]:hover {{
    background: {surface_alt};
}}
QFrame[row="true"] QLabel[role="cell_strong"] {{
    font-size: 15px;
    font-weight: 600;
}}
QFrame[listitem="true"] {{
    background: {surface};
    border: 1px solid {border};
    border-radius: 10px;
}}

/* status pills */
QLabel[tone] {{
    border: 1px solid transparent;
    border-radius: 11px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
}}
QLabel[tone="success"] {{ background: {success_soft}; color: {success}; }}
QLabel[tone="warning"] {{ background: {warning_soft}; color: {warning}; }}
QLabel[tone="danger"] {{ background: {danger_soft}; color: {danger}; }}
QLabel[tone="neutral"] {{ background: {border}; color: {text_muted}; }}
QLabel[tone="accent"] {{ background: {accent_soft}; color: {accent_pressed}; }}
QLabel[tone="info"] {{ background: {info_soft}; color: {info}; }}

QLabel[role="avatar"] {{
    background: {accent};
    color: #FFFFFF;
    border-radius: 32px;
    font-size: 26px;
    font-weight: 700;
}}
QLabel[role="card_icon"] {{
    background: {accent_soft};
    border-radius: 12px;
}}

/* stat tiles on rooms page */
QLabel[role="stat_value"] {{
    font-size: 26px;
    font-weight: 700;
}}
QLabel[role="stat_label"] {{
    color: {text_muted};
    font-size: 13px;
}}

QSizeGrip {{
    width: 14px;
    height: 14px;
}}
"""


def stylesheet():
    return _STYLESHEET.format(**COLORS)


def _pick_font_family():
    available = set(QFontDatabase().families())
    for family in FONT_FAMILIES:
        if family in available:
            return family
    return None


def apply_theme(app):
    """Apply the design system to the whole application (call once, right after QApplication is created)"""
    app.setStyle(QStyleFactory.create("Fusion"))  # same base look on every OS, the stylesheet does the rest
    family = _pick_font_family()
    font = QFont(family) if family else app.font()
    font.setPixelSize(14)
    font.setHintingPreference(QFont.PreferNoHinting)
    app.setFont(font)
    app.setStyleSheet(stylesheet())
