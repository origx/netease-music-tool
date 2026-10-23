"""ID/链接输入卡片：可选 Cookie 模式开关 + 批量/单行输入 + 「获取信息」。

无 Cookie 时提供多行批量输入框，开启 Cookie 模式后切换为单行输入框。
MDL(Basic) 不提供 Cookie 开关；MDL(Plus) 与 MVDL 页面共用完整形态。
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit

from netease_music_tool.config import TEXT_HINT
from netease_music_tool.ui import icons
from netease_music_tool.ui.components.common import Card, ToggleSwitch, make_button


class ModeInputWidget(Card):
    modeChanged = Signal(bool)
    fetchRequested = Signal()

    def __init__(
        self,
        label_batch="ID/链接列表",
        label_single="ID",
        hint_batch="无 Cookie 时可批量输入，一行一个",
        hint_single="Cookie 模式只能输入一个 ID，先获取信息再下载",
        allow_cookie=True,
        parent=None,
    ):
        super().__init__(parent, spacing=8)
        self._label_batch = label_batch
        self._hint_batch = hint_batch
        self._label_single = label_single
        self._hint_single = hint_single

        header = QHBoxLayout()
        header.setSpacing(8)
        self.label = QLabel(label_batch, objectName="CardTitle")
        header.addWidget(self.label)
        header.addStretch(1)
        self.cookie_checkbox = ToggleSwitch("Cookie 模式")
        self.cookie_checkbox.toggled.connect(self._on_toggle)
        self.cookie_checkbox.setVisible(allow_cookie)
        header.addWidget(self.cookie_checkbox)
        self.body.addLayout(header)

        self.cookie_entry = QLineEdit()
        self.cookie_entry.setEchoMode(QLineEdit.Password)
        self.cookie_entry.setPlaceholderText("粘贴网易云音乐登录 Cookie")
        self.cookie_entry.addAction(icons.icon("key", TEXT_HINT), QLineEdit.LeadingPosition)
        self.cookie_entry.hide()
        self.body.addWidget(self.cookie_entry)

        self.batch_input = QPlainTextEdit()
        self.batch_input.setPlaceholderText("一行一个 ID 或网页链接")
        self.batch_input.setFixedHeight(84)
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self.batch_input)
        shortcut.setContext(Qt.WidgetShortcut)
        shortcut.activated.connect(self._request_fetch)
        self.body.addWidget(self.batch_input)

        self.single_input = QLineEdit()
        self.single_input.setPlaceholderText("输入一个 ID 或网页链接")
        self.single_input.returnPressed.connect(self._request_fetch)
        self.body.addWidget(self.single_input)

        footer = QHBoxLayout()
        footer.setSpacing(6)
        self.hint = QLabel(hint_batch, objectName="Hint")
        footer.addWidget(self.hint, 1)
        self.clear_button = make_button("清空", "ghost", "x", "清空输入")
        self.clear_button.clicked.connect(self._clear_input)
        footer.addWidget(self.clear_button)
        self.fetch_button = make_button("获取信息", "primary", "search")
        self.fetch_button.clicked.connect(self._request_fetch)
        footer.addWidget(self.fetch_button)
        self.body.addLayout(footer)

        self._apply_mode(notify=False)

    def _on_toggle(self, enabled):
        self.cookie_entry.setVisible(enabled)
        self._clear_input()
        self._apply_mode(notify=True)

    def _apply_mode(self, notify):
        enabled = self.cookie_checkbox.isChecked()
        self.label.setText(self._label_single if enabled else self._label_batch)
        self.batch_input.setVisible(not enabled)
        self.single_input.setVisible(enabled)
        if enabled:
            self.hint.setText(f"{self._hint_single} · 回车获取")
        else:
            self.hint.setText(f"{self._hint_batch} · Ctrl+Enter 获取")
        if notify:
            self.modeChanged.emit(enabled)

    def _clear_input(self):
        self.batch_input.clear()
        self.single_input.clear()

    def _request_fetch(self):
        if self.fetch_button.isEnabled():
            self.fetchRequested.emit()

    def set_busy(self, busy):
        for widget in (self.fetch_button, self.cookie_checkbox, self.clear_button):
            widget.setEnabled(not busy)

    def is_cookie_mode(self):
        return self.cookie_checkbox.isChecked()

    def get_input_text(self):
        if self.is_cookie_mode():
            return self.single_input.text()
        return self.batch_input.toPlainText()

    def get_cookie(self):
        return self.cookie_entry.text().strip() if self.is_cookie_mode() else ""
