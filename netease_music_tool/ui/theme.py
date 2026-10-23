from string import Template

from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

import netease_music_tool.config as config
from netease_music_tool.config import (
    BG_DARK,
    BG_INPUT,
    BG_PANEL,
    BORDER,
    FONT_FAMILIES,
    PRIMARY_BLUE,
    PRIMARY_HOVER,
    SELECT_BG,
    SELECT_FG,
    TEXT_DISABLED,
    TEXT_HINT,
    TEXT_NORMAL,
    TEXT_WHITE,
)

# 界面层补充的配色 token，组件绘制时也会引用。
SIDEBAR_BG = "#191919"
CARD_BG = BG_PANEL
CARD_BORDER = "#303030"
FIELD_BG = "#1C1C1C"
FIELD_BORDER = "#3A3A3A"
BUTTON_BG = BG_INPUT
BUTTON_HOVER = "#3E3E3E"
DIVIDER = "#323232"
MENU_BG = "#2C2C2C"
ACCENT_TEXT = "#5AA9FF"
DANGER = "#F85149"
SUCCESS = "#3FB950"
ROW_HOVER = (255, 255, 255, 12)
ROW_SELECTED = (31, 122, 219, 58)
SCROLL_HANDLE = "#4A4A4A"
SCROLL_HANDLE_HOVER = "#5A5A5A"


def resolve_font_family():
    """按本机已安装字体选择中文无衬线字体，找不到时回退到系统默认字体。"""
    available = set(QFontDatabase.families())
    for family in FONT_FAMILIES:
        if family in available:
            return family
    return QApplication.font().family()


def _build_palette():
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(BG_DARK))
    palette.setColor(QPalette.WindowText, QColor(TEXT_NORMAL))
    palette.setColor(QPalette.Base, QColor(FIELD_BG))
    palette.setColor(QPalette.AlternateBase, QColor(CARD_BG))
    palette.setColor(QPalette.Text, QColor(TEXT_NORMAL))
    palette.setColor(QPalette.Button, QColor(BUTTON_BG))
    palette.setColor(QPalette.ButtonText, QColor(TEXT_NORMAL))
    palette.setColor(QPalette.Highlight, QColor(SELECT_BG))
    palette.setColor(QPalette.HighlightedText, QColor(SELECT_FG))
    palette.setColor(QPalette.PlaceholderText, QColor(TEXT_HINT))
    palette.setColor(QPalette.ToolTipBase, QColor(MENU_BG))
    palette.setColor(QPalette.ToolTipText, QColor(TEXT_NORMAL))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(TEXT_DISABLED))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(TEXT_DISABLED))
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(TEXT_DISABLED))
    return palette


_STYLESHEET = Template(
    """
QMainWindow, QDialog {
    background-color: $bg_dark;
}

QLabel {
    background: transparent;
}

QLabel#PageTitle {
    color: $text_white;
    font-size: 15pt;
    font-weight: 600;
}

QLabel#Hint {
    color: $text_hint;
}

QLabel#CardTitle {
    color: $text_white;
    font-weight: 600;
}

QLabel#CountBadge {
    background-color: $button_bg;
    border-radius: 9px;
    color: $text_hint;
    font-size: 8pt;
    padding: 1px 8px;
}

QLabel#SectionLabel {
    color: $text_hint;
    font-size: 8pt;
    padding: 0 10px;
}

QLabel#BrandLogo {
    background-color: $primary;
    border-radius: 9px;
}

QLabel#BrandTitle {
    color: $text_white;
    font-size: 10pt;
    font-weight: 600;
}

QLabel#BrandSub {
    color: $text_hint;
    font-size: 8pt;
}

QLabel#BannerText {
    color: #FF8A80;
}

QLabel#StatusLabel {
    color: $text_hint;
    padding: 2px 6px;
}

QFrame#Sidebar {
    background-color: $sidebar_bg;
    border: none;
    border-right: 1px solid $divider;
}

QFrame#Card {
    background-color: $card_bg;
    border: 1px solid $card_border;
    border-radius: 12px;
}

QFrame#Card[dropActive="true"] {
    border: 1px dashed $primary;
}

QFrame#Banner {
    background-color: rgba(248, 81, 73, 0.10);
    border: 1px solid rgba(248, 81, 73, 0.32);
    border-radius: 8px;
}

QFrame#PathField {
    background-color: $field_bg;
    border: 1px solid $field_border;
    border-radius: 8px;
}

QPushButton, QToolButton {
    background-color: $button_bg;
    border: none;
    border-radius: 8px;
    color: $text;
    min-height: 18px;
    padding: 5px 12px;
}

QPushButton:hover, QToolButton:hover {
    background-color: $button_hover;
    color: $text_white;
}

QPushButton:pressed, QToolButton:pressed {
    background-color: $button_bg;
}

QPushButton:disabled, QToolButton:disabled {
    background-color: #2C2C2C;
    color: $text_disabled;
}

QToolButton::menu-indicator {
    image: none;
    width: 0;
}

QPushButton[variant="primary"] {
    background-color: $primary;
    color: $text_white;
    font-weight: 600;
    padding: 5px 16px;
}

QPushButton[variant="primary"]:hover {
    background-color: $primary_hover;
}

QPushButton[variant="primary"]:disabled {
    background-color: #23405E;
    color: #7F97B0;
}

QPushButton[variant="ghost"], QToolButton[variant="ghost"],
QPushButton[variant="danger"] {
    background-color: transparent;
}

QPushButton[variant="ghost"]:hover, QToolButton[variant="ghost"]:hover {
    background-color: $button_bg;
}

QPushButton[variant="danger"]:hover {
    background-color: rgba(248, 81, 73, 0.14);
    color: $danger;
}

QPushButton[variant="ghost"]:disabled, QToolButton[variant="ghost"]:disabled,
QPushButton[variant="danger"]:disabled {
    background-color: transparent;
}

QPushButton#NavButton {
    background-color: transparent;
    border-radius: 8px;
    color: $text;
    padding: 8px 10px;
    text-align: left;
}

QPushButton#NavButton:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: $text_white;
}

QPushButton#NavButton:checked {
    background-color: rgba(31, 122, 219, 0.18);
    color: $accent_text;
    font-weight: 600;
}

QLineEdit, QPlainTextEdit {
    background-color: $field_bg;
    border: 1px solid $field_border;
    border-radius: 8px;
    color: $text;
    padding: 5px 8px;
    selection-background-color: $select_bg;
    selection-color: $select_fg;
}

QPlainTextEdit {
    padding: 4px 6px;
}

QLineEdit:focus, QPlainTextEdit:focus {
    border-color: $primary;
}

QLineEdit#BareEdit {
    background: transparent;
    border: none;
    padding: 5px 2px;
}

QCheckBox {
    background: transparent;
    color: $text;
    spacing: 6px;
}

QCheckBox::indicator {
    background-color: $field_bg;
    border: 1px solid #555555;
    border-radius: 4px;
    width: 15px;
    height: 15px;
}

QCheckBox::indicator:hover {
    border-color: $primary;
}

QCheckBox::indicator:checked, QCheckBox::indicator:indeterminate {
    background-color: $primary;
    border-color: $primary;
}

QTableWidget {
    background-color: $card_bg;
    border: none;
    color: $text;
    gridline-color: transparent;
    outline: 0;
}

QHeaderView {
    background-color: transparent;
    border: none;
}

QHeaderView::section {
    background-color: $card_bg;
    border: none;
    border-bottom: 1px solid $divider;
    color: $text_hint;
    font-size: 8.5pt;
    padding: 0 10px;
}

QTableCornerButton::section {
    background-color: $card_bg;
    border: none;
}

QScrollBar:vertical {
    background: transparent;
    margin: 2px;
    width: 10px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background-color: $scroll_handle;
    border-radius: 3px;
    min-height: 30px;
}

QScrollBar::handle:horizontal {
    background-color: $scroll_handle;
    border-radius: 3px;
    min-width: 30px;
}

QScrollBar::handle:hover {
    background-color: $scroll_handle_hover;
}

QScrollBar::add-line, QScrollBar::sub-line {
    height: 0;
    width: 0;
}

QScrollBar::add-page, QScrollBar::sub-page {
    background: transparent;
}

QMenu {
    background-color: $menu_bg;
    border: 1px solid $field_border;
    border-radius: 10px;
    padding: 5px;
}

QMenu::item {
    background: transparent;
    border-radius: 6px;
    color: $text;
    padding: 6px 24px 6px 12px;
}

QMenu::item:selected {
    background-color: rgba(31, 122, 219, 0.28);
    color: $text_white;
}

QMenu::item:disabled {
    color: $text_disabled;
}

QMenu::separator {
    background-color: $divider;
    height: 1px;
    margin: 4px 6px;
}

QStatusBar {
    background-color: $sidebar_bg;
    border-top: 1px solid $divider;
    color: $text_hint;
}

QStatusBar::item {
    border: none;
}

QToolTip {
    background-color: $menu_bg;
    border: 1px solid $field_border;
    border-radius: 6px;
    color: $text;
    padding: 4px 8px;
}
"""
)


def _build_stylesheet():
    return _STYLESHEET.substitute(
        bg_dark=BG_DARK,
        sidebar_bg=SIDEBAR_BG,
        card_bg=CARD_BG,
        card_border=CARD_BORDER,
        field_bg=FIELD_BG,
        field_border=FIELD_BORDER,
        button_bg=BUTTON_BG,
        button_hover=BUTTON_HOVER,
        divider=DIVIDER,
        menu_bg=MENU_BG,
        border=BORDER,
        primary=PRIMARY_BLUE,
        primary_hover=PRIMARY_HOVER,
        accent_text=ACCENT_TEXT,
        text=TEXT_NORMAL,
        text_white=TEXT_WHITE,
        text_hint=TEXT_HINT,
        text_disabled=TEXT_DISABLED,
        select_bg=SELECT_BG,
        select_fg=SELECT_FG,
        danger=DANGER,
        scroll_handle=SCROLL_HANDLE,
        scroll_handle_hover=SCROLL_HANDLE_HOVER,
    )


def apply_theme(app):
    """应用字体、调色板和全局样式表，并同步 config.FONT_FAMILY。"""
    family = resolve_font_family()
    config.FONT_FAMILY = family
    app.setFont(QFont(family, 9))
    app.setPalette(_build_palette())
    app.setStyleSheet(_build_stylesheet())
    return family
