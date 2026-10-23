"""NCM 转换列表组件。

NCM2MP3 页面使用。显示封面缩略图、歌名、歌手、时长、转换大小、状态；
支持拖入 .ncm 文件、多选、删除选中、清空、转换选中项。新添加的文件自动勾选。
"""

from PySide6.QtCore import QItemSelectionModel, QRect, Qt, Signal
from PySide6.QtGui import QPixmap

from netease_music_tool.ui.components.common import make_button
from netease_music_tool.ui.components.selectable_list import SelectableListCard

COLUMNS = (
    ("cover", "封面", 56),
    ("title", "歌名", None),
    ("artist", "歌手", 150),
    ("duration", "时长", 72),
    ("size", "转换大小", 96),
    ("status", "状态", 140),
)


def _ncm_paths(mime_data):
    if not mime_data.hasUrls():
        return []
    return [
        url.toLocalFile()
        for url in mime_data.urls()
        if url.isLocalFile() and url.toLocalFile().lower().endswith(".ncm")
    ]


class ConvertListWidget(SelectableListCard):
    addRequested = Signal()
    convertRequested = Signal()
    filesDropped = Signal(list)
    add_button = None

    def __init__(self, status_label=None, thumb_size=40, parent=None):
        super().__init__(
            COLUMNS,
            status_label=status_label,
            title="文件列表",
            primary_text="转换选中",
            primary_icon="repeat",
            empty_text="拖入 .ncm 文件，或点击「添加文件」",
            row_height=thumb_size + 12,
            pending_label="待转换项",
            parent=parent,
        )
        self._thumb_size = thumb_size
        self.add_button = make_button("添加文件", "secondary", "plus")
        self.add_button.clicked.connect(lambda: self.addRequested.emit())
        self.add_toolbar_widget(self.add_button)
        self.primaryRequested.connect(self.convertRequested)
        self.setAcceptDrops(True)

    def _refresh(self):
        super()._refresh()
        if self.add_button is not None:
            self.add_button.setEnabled(not self._busy)

    def add_row(self, record):
        """record: 含 title/artist/duration_text/size_text/cover(字节) 等字段。"""
        self.rows.append(record)
        row = len(self.rows) - 1
        self.table.insertRow(row)
        self.fill_row(
            row,
            (
                "",
                record.get("title", ""),
                record.get("artist", ""),
                record.get("duration_text", "00:00"),
                record.get("size_text", "-"),
                "待转换",
            ),
        )
        cover = self._make_thumb(record.get("cover"))
        if cover is not None:
            self.table.item(row, self.table.column_of("cover")).setData(Qt.UserRole, cover)
        self.table.select_rows([row], QItemSelectionModel.SelectionFlag.Select)

    def _make_thumb(self, data):
        """裁成正方形并按 2 倍尺寸缩放，交给表格圆角绘制。"""
        if not data:
            return None
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            return None
        size = self._thumb_size * 2
        pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        return pixmap.copy(QRect((pixmap.width() - size) // 2, (pixmap.height() - size) // 2, size, size))

    def set_size(self, row, text):
        self.set_cell(row, "size", text)

    def _set_drop_active(self, active):
        self.setProperty("dropActive", active)
        self.style().unpolish(self)
        self.style().polish(self)

    def dragEnterEvent(self, event):
        if not self._busy and _ncm_paths(event.mimeData()):
            event.acceptProposedAction()
            self._set_drop_active(True)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._set_drop_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._set_drop_active(False)
        paths = _ncm_paths(event.mimeData())
        if paths:
            event.acceptProposedAction()
            self.filesDropped.emit(paths)
