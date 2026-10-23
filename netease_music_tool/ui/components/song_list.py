"""多选下载列表组件。

MDL(Basic)、MDL(Plus)、MVDL 页面共用。获取信息后自动勾选可下载项；
开启 Cookie 单曲模式时隐藏勾选与批量操作，只保留「下载」。
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QAbstractItemView

from netease_music_tool.ui.components.selectable_list import SelectableListCard

# (key, 标题, 宽度)；宽度为 None 的列自动拉伸。
DEFAULT_COLUMNS = (
    ("id", "歌曲 ID", None),
    ("size", "文件大小", 140),
    ("status", "状态", 170),
)


class SongListWidget(SelectableListCard):
    downloadRequested = Signal()
    _single_mode = False

    def __init__(
        self,
        status_label=None,
        columns=DEFAULT_COLUMNS,
        title="歌曲列表",
        download_text="下载选中",
        empty_text="输入 ID 或链接后点击「获取信息」",
        single_mode=False,
        parent=None,
    ):
        super().__init__(
            columns,
            status_label=status_label,
            title=title,
            primary_text=download_text,
            primary_icon="download",
            empty_text=empty_text,
            pending_label="可下载项",
            parent=parent,
        )
        self.primaryRequested.connect(self.downloadRequested)
        self.set_single_mode(single_mode)

    def set_single_mode(self, single):
        self._single_mode = bool(single)
        self.table.clearSelection()
        self.table.setColumnHidden(0, self._single_mode)
        self.table.setSelectionMode(
            QAbstractItemView.NoSelection if self._single_mode else QAbstractItemView.ExtendedSelection
        )
        for widget in (self.count_label, self.select_button, self.delete_button, self.clear_button):
            widget.setVisible(not self._single_mode)
        self._refresh()

    def _primary_ready(self, count):
        return bool(self.rows) if self._single_mode else count > 0

    def _primary_label(self, count):
        return "下载" if self._single_mode else super()._primary_label(count)

    def populate(self, infos, format_row):
        """用条目列表重建表格并自动勾选可下载项。format_row(info) 返回一行的值元组。"""
        self.rows = list(infos)
        self.table.setRowCount(0)
        self.table.setRowCount(len(self.rows))
        for row, info in enumerate(self.rows):
            self.fill_row(row, format_row(info))
        if not self._single_mode:
            self.select_pending()
        self._refresh()
