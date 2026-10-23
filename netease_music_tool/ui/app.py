import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from netease_music_tool.config import APP_TITLE, TEXT_WHITE, WINDOW_MIN_SIZE, WINDOW_SIZE
from netease_music_tool.ui import icons
from netease_music_tool.ui.components.navigation import create_nav_item
from netease_music_tool.ui.pages.music_dl_basic import build_page as build_basic_page
from netease_music_tool.ui.pages.music_dl_plus import build_page as build_plus_page
from netease_music_tool.ui.pages.mvdl import build_page as build_mvdl_page
from netease_music_tool.ui.pages.ncm_to_mp3 import build_page as build_ncm_page
from netease_music_tool.ui.theme import apply_theme

# (标题, 图标, 提示)
NAV_ITEMS = (
    ("MDL(Basic)", "music", "基础下载(基于旧版官方 API)"),
    ("MDL(Plus)", "zap", "增强下载(模拟安卓端eapi,支持 Cookie)"),
    ("NCM2MP3", "repeat", "NCM 格式转换"),
    ("MVDL", "video", "MV 视频下载"),
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(*WINDOW_SIZE)
        self.setMinimumSize(*WINDOW_MIN_SIZE)

        central = QWidget()
        self.setCentralWidget(central)
        body = QHBoxLayout(central)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        body.addWidget(self._build_sidebar())

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 18, 20, 16)
        content_layout.setSpacing(0)
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        body.addWidget(content, 1)

        self.status_label = QLabel("就绪", objectName="StatusLabel")
        status_bar = self.statusBar()
        status_bar.setSizeGripEnabled(False)
        status_bar.addWidget(self.status_label, 1)

        self._build_pages()
        self.switch_page(0)

    def _build_sidebar(self):
        sidebar = QFrame(objectName="Sidebar")
        sidebar.setFixedWidth(196)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(4)

        layout.addWidget(QLabel("功能", objectName="SectionLabel"))
        layout.addSpacing(2)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self._nav_buttons = []
        for index, (title, icon_name, tooltip) in enumerate(NAV_ITEMS):
            button = create_nav_item(layout, title, index, icon_name, tooltip)
            button.clicked.connect(lambda _checked=False, i=index: self.switch_page(i))
            self.nav_group.addButton(button, index)
            self._nav_buttons.append(button)
        layout.addStretch(1)
        return sidebar

    def _build_pages(self):
        self.pages = [
            build_basic_page(self.stack, self.status_label),
            build_plus_page(self.stack, self.status_label),
            build_ncm_page(self.stack, self.status_label),
            build_mvdl_page(self.stack, self.status_label),
        ]
        for page in self.pages:
            self.stack.addWidget(page)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        self._nav_buttons[index].setChecked(True)


def run_app():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    apply_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    run_app()
