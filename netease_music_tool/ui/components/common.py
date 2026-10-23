"""页面通用控件：卡片、标题区、按钮、菜单、保存目录选择行、复选框与开关。"""

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QStyle,
    QStyleOptionButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from netease_music_tool.config import (
    PRIMARY_BLUE,
    TEXT_DISABLED,
    TEXT_HINT,
    TEXT_NORMAL,
    TEXT_WHITE,
)
from netease_music_tool.ui import icons
from netease_music_tool.ui.theme import DANGER, FIELD_BG

_ICON_COLORS = {"primary": TEXT_WHITE, "danger": TEXT_NORMAL}


def set_button_text(button, text):
    """带图标的按钮在文字前补一个空格，拉开图标与文字的间距。"""
    button.setText(f" {text}" if text and not button.icon().isNull() else text)


def make_button(text, variant="secondary", icon_name=None, tooltip=None):
    """圆角按钮。variant: primary / secondary / ghost / danger。"""
    button = QPushButton()
    button.setProperty("variant", variant)
    button.setCursor(Qt.PointingHandCursor)
    if icon_name:
        color = _ICON_COLORS.get(variant, TEXT_NORMAL)
        button.setIcon(icons.icon(icon_name, color, disabled_color=TEXT_DISABLED))
        button.setIconSize(QSize(15, 15))
    set_button_text(button, text)
    if tooltip:
        button.setToolTip(tooltip)
    return button


def make_menu(parent=None):
    """圆角弹出菜单（需要透明背景才能显示真正的圆角）。"""
    menu = QMenu(parent)
    menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
    menu.setAttribute(Qt.WA_TranslucentBackground)
    return menu


def make_menu_button(text, icon_name, menu):
    button = QToolButton()
    button.setText(f" {text}")
    button.setIcon(icons.icon(icon_name, TEXT_NORMAL, disabled_color=TEXT_DISABLED))
    button.setIconSize(QSize(15, 15))
    button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    button.setPopupMode(QToolButton.InstantPopup)
    button.setProperty("variant", "ghost")
    button.setCursor(Qt.PointingHandCursor)
    button.setMenu(menu)
    return button


def icon_label(name, color, size=16):
    label = QLabel()
    label.setPixmap(icons.pixmap(name, color, size))
    label.setFixedSize(size, size)
    return label


class Card(QFrame):
    """圆角卡片容器，内容通过 body 布局添加。"""

    def __init__(self, parent=None, margins=(14, 12, 14, 12), spacing=10):
        super().__init__(parent, objectName="Card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(*margins)
        self.body.setSpacing(spacing)


class CheckBox(QCheckBox):
    """在样式表绘制的方形指示器上补画对勾 / 横线（QSS 无法绘制勾选标记）。"""

    def paintEvent(self, event):
        super().paintEvent(event)
        state = self.checkState()
        if state == Qt.Unchecked:
            return
        option = QStyleOptionButton()
        self.initStyleOption(option)
        rect = self.style().subElementRect(QStyle.SE_CheckBoxIndicator, option, self)
        pen = QPen(QColor(TEXT_WHITE), 2.0)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(pen)
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        if state == Qt.PartiallyChecked:
            painter.drawLine(QPointF(x + w * 0.28, y + h * 0.5), QPointF(x + w * 0.72, y + h * 0.5))
        else:
            painter.drawPolyline(
                [
                    QPointF(x + w * 0.22, y + h * 0.52),
                    QPointF(x + w * 0.42, y + h * 0.72),
                    QPointF(x + w * 0.80, y + h * 0.30),
                ]
            )
        painter.end()


class ToggleSwitch(QCheckBox):
    """开关样式的复选框，保留 QCheckBox 的 toggled / isChecked 接口。"""

    TRACK_W = 32
    TRACK_H = 18
    GAP = 8

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)

    def sizeHint(self):
        metrics = self.fontMetrics()
        width = self.TRACK_W
        if self.text():
            width += self.GAP + metrics.horizontalAdvance(self.text())
        return QSize(width + 2, max(self.TRACK_H, metrics.height()) + 4)

    def minimumSizeHint(self):
        return self.sizeHint()

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        on = self.isChecked()
        h = self.TRACK_H
        track = QRectF(1, (self.height() - h) / 2, self.TRACK_W, h)
        if on:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(PRIMARY_BLUE))
        else:
            painter.setPen(QPen(QColor("#555555"), 1))
            painter.setBrush(QColor(FIELD_BG))
        painter.drawRoundedRect(track, h / 2, h / 2)

        knob = h - 6
        knob_x = track.right() - knob - 3 if on else track.left() + 3
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(TEXT_WHITE if on else TEXT_HINT))
        painter.drawEllipse(QRectF(knob_x, track.top() + 3, knob, knob))

        if self.text():
            painter.setPen(QColor(TEXT_NORMAL if self.isEnabled() else TEXT_DISABLED))
            text_rect = QRectF(self.TRACK_W + self.GAP + 1, 0, self.width(), self.height())
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self.text())
        painter.end()


class PageHeader(QWidget):
    """页面标题 + 副标题，可选红色提示横幅。"""

    def __init__(self, title, subtitle=None, warning=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(QLabel(title, objectName="PageTitle"))
        if subtitle:
            layout.addWidget(QLabel(subtitle, objectName="Hint", wordWrap=True))
        if warning:
            layout.addSpacing(8)
            banner = QFrame(objectName="Banner")
            row = QHBoxLayout(banner)
            row.setContentsMargins(10, 6, 10, 6)
            row.setSpacing(8)
            row.addWidget(icon_label("alert", DANGER, 14))
            row.addWidget(QLabel(warning, objectName="BannerText", wordWrap=True), 1)
            layout.addWidget(banner)


class PathPicker(QFrame):
    """保存目录输入行：文件夹图标 + 文本框 + 更改按钮。"""

    def __init__(self, dialog_title, initial_path="", parent=None):
        super().__init__(parent, objectName="PathField")
        self._dialog_title = dialog_title
        self.setToolTip("保存目录")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 3, 2)
        layout.setSpacing(6)
        layout.addWidget(icon_label("folder", TEXT_HINT, 15))
        self.edit = QLineEdit(initial_path, objectName="BareEdit")
        self.edit.setPlaceholderText("保存目录")
        layout.addWidget(self.edit, 1)
        self.button = make_button("更改", "ghost")
        self.button.setToolTip("选择保存目录")
        self.button.clicked.connect(self._choose)
        layout.addWidget(self.button)

    def _choose(self):
        folder = QFileDialog.getExistingDirectory(self, self._dialog_title, self.path())
        if folder:
            self.edit.setText(folder)

    def path(self):
        return self.edit.text().strip()
