"""侧边栏导航项。"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QPushButton

from netease_music_tool.config import TEXT_NORMAL
from netease_music_tool.ui import icons
from netease_music_tool.ui.theme import ACCENT_TEXT


def create_nav_item(parent_layout, text, index, icon_name=None, tooltip=None):
    """创建可选中导航按钮并加入侧边栏布局，返回按钮实例。"""
    button = QPushButton(text, objectName="NavButton")
    button.setCheckable(True)
    button.setCursor(Qt.PointingHandCursor)
    button.setProperty("nav_index", index)
    if icon_name:
        button.setIcon(icons.icon(icon_name, TEXT_NORMAL, checked_color=ACCENT_TEXT))
        button.setIconSize(QSize(16, 16))
    if tooltip:
        button.setToolTip(tooltip)
    parent_layout.addWidget(button)
    return button
