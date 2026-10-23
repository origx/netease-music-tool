"""可勾选列表卡片：工具栏 + 勾选表格 + 底部操作栏。

交互约定：单击行即勾选/取消，Shift+单击连选，表头勾选框或 Ctrl+A 全选，
空格切换当前行，Delete 删除选中；「选择」菜单与右键菜单提供反选、
按状态筛选等批量选择。SongListWidget / ConvertListWidget 在此基础上扩展。
"""

from PySide6.QtCore import QEvent, QItemSelection, QItemSelectionModel, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QPainter, QPainterPath, QPen, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QStyle,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from netease_music_tool.config import PRIMARY_BLUE, TEXT_HINT, TEXT_NORMAL, TEXT_WHITE
from netease_music_tool.ui import icons
from netease_music_tool.ui.components.common import make_button, make_menu, make_menu_button, set_button_text
from netease_music_tool.ui.theme import (
    ACCENT_TEXT,
    DANGER,
    FIELD_BG,
    ROW_HOVER,
    ROW_SELECTED,
    SUCCESS,
)

CHECK_KEY = "_check"
PENDING_STATUSES = ("可下载", "待转换")
_SelectionFlag = QItemSelectionModel.SelectionFlag
_TONE_COLORS = {
    "success": SUCCESS,
    "danger": DANGER,
    "active": ACCENT_TEXT,
    "muted": TEXT_HINT,
}


def status_tone(text):
    if "失败" in text:
        return "danger"
    if "完成" in text or text == "可下载":
        return "success"
    if text.endswith("中") or text.endswith("..."):
        return "active"
    return "muted"


def paint_check_box(painter, rect, state):
    """在 rect 中心绘制 16px 圆角勾选框，state 为 Qt.CheckState。"""
    size = 16
    box = QRectF(rect.center().x() - size / 2 + 0.5, rect.center().y() - size / 2 + 0.5, size, size)
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)
    if state == Qt.Unchecked:
        painter.setPen(QPen(QColor("#5A5A5A"), 1.2))
        painter.setBrush(QColor(FIELD_BG))
        painter.drawRoundedRect(box.adjusted(0.5, 0.5, -0.5, -0.5), 4, 4)
    else:
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(PRIMARY_BLUE))
        painter.drawRoundedRect(box, 4, 4)
        pen = QPen(QColor(TEXT_WHITE), 2.0)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        x, y = box.x(), box.y()
        if state == Qt.PartiallyChecked:
            painter.drawLine(QPointF(x + 4.5, y + 8), QPointF(x + 11.5, y + 8))
        else:
            painter.drawPolyline(
                [QPointF(x + 3.8, y + 8.3), QPointF(x + 6.8, y + 11.2), QPointF(x + 12.4, y + 5.0)]
            )
    painter.restore()


class _RowDelegate(QStyledItemDelegate):
    """整行圆角背景 + 勾选框 / 封面 / 状态标签 / 文本的统一绘制。"""

    def __init__(self, table):
        super().__init__(table)
        self._table = table

    def paint(self, painter, option, index):
        table = self._table
        key = table.column_key(index.column())
        selected = bool(option.state & QStyle.State_Selected)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        background = ROW_SELECTED if selected else ROW_HOVER if index.row() == table.hover_row else None
        if background is not None:
            viewport = table.viewport().rect()
            row_rect = QRectF(viewport.left() + 2, option.rect.top() + 2, viewport.width() - 4, option.rect.height() - 4)
            painter.setClipRect(option.rect)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(*background))
            painter.drawRoundedRect(row_rect, 8, 8)
            painter.setClipping(False)

        text = index.data(Qt.DisplayRole) or ""
        if key == CHECK_KEY:
            paint_check_box(painter, option.rect, Qt.Checked if selected else Qt.Unchecked)
        elif key == "cover":
            self._paint_cover(painter, option.rect, index.data(Qt.UserRole))
        elif key == "status":
            self._paint_status(painter, option, text)
        else:
            rect = option.rect.adjusted(10, 0, -8, 0)
            painter.setPen(QColor(TEXT_WHITE if selected else TEXT_NORMAL))
            painter.drawText(rect, Qt.AlignVCenter | Qt.AlignLeft, option.fontMetrics.elidedText(text, Qt.ElideRight, rect.width()))
        painter.restore()

    def _paint_cover(self, painter, rect, pixmap):
        size = min(rect.height() - 10, rect.width() - 10)
        target = QRectF(rect.x() + (rect.width() - size) / 2, rect.y() + (rect.height() - size) / 2, size, size)
        path = QPainterPath()
        path.addRoundedRect(target, 6, 6)
        if pixmap is not None and not pixmap.isNull():
            painter.setClipPath(path)
            painter.drawPixmap(target, pixmap, QRectF(pixmap.rect()))
            painter.setClipping(False)
        else:
            painter.fillPath(path, QColor(FIELD_BG))
            painter.drawPixmap(
                QPointF(target.center().x() - 8, target.center().y() - 8),
                icons.pixmap("music", TEXT_HINT, 16),
            )

    def _paint_status(self, painter, option, text):
        if not text:
            return
        color = QColor(_TONE_COLORS[status_tone(text)])
        metrics = option.fontMetrics
        elided = metrics.elidedText(text, Qt.ElideRight, max(0, option.rect.width() - 50))
        chip = QRectF(option.rect.x() + 8, option.rect.center().y() - 10.5, metrics.horizontalAdvance(elided) + 28, 21)
        tint = QColor(color)
        tint.setAlpha(36)
        painter.setPen(Qt.NoPen)
        painter.setBrush(tint)
        painter.drawRoundedRect(chip, 10.5, 10.5)
        painter.setBrush(color)
        painter.drawEllipse(QPointF(chip.x() + 10, chip.center().y()), 3, 3)
        painter.setPen(color)
        painter.drawText(chip.adjusted(18, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, elided)


class _CheckHeader(QHeaderView):
    """第 0 列表头绘制全选勾选框（全选 / 部分 / 未选）。"""

    def __init__(self, table):
        super().__init__(Qt.Horizontal, table)
        self._table = table

    def paintSection(self, painter, rect, logical_index):
        painter.save()
        super().paintSection(painter, rect, logical_index)
        painter.restore()
        if logical_index == 0 and self._table.rowCount():
            paint_check_box(painter, rect, self._table.check_state())


class SelectableTable(QTableWidget):
    """首列为勾选框的表格，选中状态即勾选状态。"""

    def __init__(self, columns, row_height=40, empty_text="", parent=None):
        self._keys = [CHECK_KEY] + [key for key, _title, _width in columns]
        super().__init__(0, len(self._keys), parent)
        self.hover_row = -1
        self._empty_text = empty_text

        self.setItemDelegate(_RowDelegate(self))
        self.setHorizontalHeader(_CheckHeader(self))
        self.setFrameShape(QFrame.NoFrame)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setMouseTracking(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(row_height)

        header = self.horizontalHeader()
        header.setFixedHeight(32)
        header.setHighlightSections(False)
        header.setSectionsClickable(True)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.sectionClicked.connect(self._on_header_clicked)
        self.setHorizontalHeaderItem(0, QTableWidgetItem(""))
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.setColumnWidth(0, 40)
        for index, (_key, title, width) in enumerate(columns, start=1):
            self.setHorizontalHeaderItem(index, QTableWidgetItem(title))
            if width is None:
                header.setSectionResizeMode(index, QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(index, QHeaderView.Interactive)
                self.setColumnWidth(index, width)

    def column_key(self, column):
        return self._keys[column]

    def column_of(self, key):
        return self._keys.index(key)

    def selected_rows(self):
        return sorted({index.row() for index in self.selectionModel().selectedIndexes()})

    def check_state(self):
        count = len(self.selected_rows())
        if count == 0:
            return Qt.Unchecked
        return Qt.Checked if count == self.rowCount() else Qt.PartiallyChecked

    def select_rows(self, rows, mode=_SelectionFlag.ClearAndSelect):
        selection = QItemSelection()
        last = self.columnCount() - 1
        for row in rows:
            selection.select(self.model().index(row, 0), self.model().index(row, last))
        self.selectionModel().select(selection, mode)

    def _on_header_clicked(self, section):
        if section != 0 or self.selectionMode() == QAbstractItemView.NoSelection:
            return
        if self.check_state() == Qt.Checked:
            self.clearSelection()
        else:
            self.selectAll()

    def selectionCommand(self, index, event=None):
        """普通单击 = 切换勾选，拖动/松开不改动已有勾选；Shift/Ctrl 保留默认的连选/切换。"""
        if event is not None and self.selectionMode() == QAbstractItemView.ExtendedSelection:
            kind = event.type()
            modifiers = event.modifiers()
            if kind == QEvent.MouseButtonPress and not modifiers & (Qt.ShiftModifier | Qt.ControlModifier):
                return _SelectionFlag.Toggle | _SelectionFlag.Rows
            if kind in (QEvent.MouseMove, QEvent.MouseButtonRelease) and not modifiers & Qt.ShiftModifier:
                return _SelectionFlag.NoUpdate
            if kind == QEvent.KeyPress:
                if event.key() == Qt.Key_Space:
                    return _SelectionFlag.Toggle | _SelectionFlag.Rows
                if not modifiers & Qt.ShiftModifier:
                    return _SelectionFlag.NoUpdate
        return super().selectionCommand(index, event)

    def mouseMoveEvent(self, event):
        self._set_hover(self.rowAt(event.position().toPoint().y()))
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._set_hover(-1)
        super().leaveEvent(event)

    def _set_hover(self, row):
        if row != self.hover_row:
            self.hover_row = row
            self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.rowCount() or not self._empty_text:
            return
        painter = QPainter(self.viewport())
        rect = self.viewport().rect()
        center = rect.center()
        painter.drawPixmap(QPointF(center.x() - 18, center.y() - 34), icons.pixmap("inbox", "#5A5A5A", 36, 1.5))
        painter.setPen(QColor(TEXT_HINT))
        painter.drawText(QRectF(rect.left(), center.y() + 10, rect.width(), 24), Qt.AlignHCenter | Qt.AlignTop, self._empty_text)
        painter.end()


class SelectableListCard(QFrame):
    primaryRequested = Signal()

    def __init__(
        self,
        columns,
        status_label=None,
        title="列表",
        primary_text="确定",
        primary_icon=None,
        empty_text="",
        row_height=40,
        pending_label="待处理项",
        parent=None,
    ):
        super().__init__(parent, objectName="Card")
        self.status_label = status_label
        self.rows = []
        self._busy = False
        self._primary_text = primary_text
        self._pending_label = pending_label

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(6)

        self.toolbar = QHBoxLayout()
        self.toolbar.setSpacing(6)
        self.toolbar.addWidget(QLabel(title, objectName="CardTitle"))
        self.count_label = QLabel(objectName="CountBadge")
        self.toolbar.addWidget(self.count_label)
        self.toolbar.addStretch(1)
        self.select_button = make_menu_button("选择", "list-checks", self._build_selection_menu(make_menu(self)))
        self.delete_button = make_button("删除", "danger", "trash", "删除选中项 (Delete)")
        self.delete_button.clicked.connect(lambda: self.delete_selected())
        self.clear_button = make_button("清空", "ghost", "x", "清空整个列表")
        self.clear_button.clicked.connect(lambda: self.clear_all())
        for widget in (self.select_button, self.delete_button, self.clear_button):
            self.toolbar.addWidget(widget)
        layout.addLayout(self.toolbar)

        self.table = SelectableTable(columns, row_height, empty_text)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.selectionModel().selectionChanged.connect(lambda *_: self._refresh())
        self.table.model().rowsInserted.connect(lambda *_: self._refresh())
        self.table.model().rowsRemoved.connect(lambda *_: self._refresh())
        shortcut = QShortcut(QKeySequence.Delete, self.table)
        shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        shortcut.activated.connect(self.delete_selected)
        layout.addWidget(self.table, 1)

        self.footer = QHBoxLayout()
        self.footer.setContentsMargins(0, 4, 0, 0)
        self.footer.setSpacing(8)
        self.primary_button = make_button(primary_text, "primary", primary_icon)
        self.primary_button.setMinimumWidth(124)
        self.primary_button.clicked.connect(lambda: self.primaryRequested.emit())
        self.footer.addWidget(self.primary_button)
        layout.addLayout(self.footer)

        self._refresh()

    # ---- 布局扩展 ----

    def add_toolbar_widget(self, widget):
        """在右侧操作区最前面插入控件（如「添加文件」）。"""
        self.toolbar.insertWidget(self.toolbar.indexOf(self.select_button), widget)

    def add_footer_widget(self, widget, stretch=0):
        """在主操作按钮左侧插入控件（如保存目录）。"""
        self.footer.insertWidget(self.footer.indexOf(self.primary_button), widget, stretch)

    # ---- 选择 ----

    def _build_selection_menu(self, menu, with_delete=False):
        entries = (
            ("全选\tCtrl+A", self.select_all),
            ("反选", self.invert_selection),
            (f"选择{self._pending_label}", self.select_pending),
            ("选择失败项", self.select_failed),
            (None, None),
            ("取消选择", self.clear_selection),
        )
        for text, slot in entries:
            if text is None:
                menu.addSeparator()
                continue
            action = menu.addAction(text)
            action.triggered.connect(lambda _checked=False, fn=slot: fn())
        if with_delete:
            menu.addSeparator()
            action = menu.addAction(icons.icon("trash", DANGER), "删除选中\tDelete")
            action.setEnabled(bool(self.selected_indices()))
            action.triggered.connect(lambda _checked=False: self.delete_selected())
        return menu

    def _show_context_menu(self, pos):
        if self._busy or not self.table.rowCount() or self.table.selectionMode() == QAbstractItemView.NoSelection:
            return
        menu = self._build_selection_menu(make_menu(self), with_delete=True)
        menu.exec(self.table.viewport().mapToGlobal(pos))
        menu.deleteLater()

    def selected_indices(self):
        return self.table.selected_rows()

    def select_all(self):
        self.table.selectAll()

    def clear_selection(self):
        self.table.clearSelection()

    def invert_selection(self):
        selected = set(self.selected_indices())
        self.table.select_rows([row for row in range(self.table.rowCount()) if row not in selected])

    def select_where(self, predicate):
        """按状态文本筛选勾选：predicate(status_text) -> bool。"""
        column = self.table.column_of("status")
        rows = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, column)
            if predicate(item.text() if item else ""):
                rows.append(row)
        self.table.select_rows(rows)
        return rows

    def select_pending(self):
        return self.select_where(lambda status: status in PENDING_STATUSES)

    def select_failed(self):
        return self.select_where(lambda status: "失败" in status)

    # ---- 单元格 ----

    def fill_row(self, row, values):
        """values 按列定义顺序（不含勾选列）给出。"""
        self.table.setItem(row, 0, QTableWidgetItem())
        for column, value in enumerate(values, start=1):
            self.set_cell(row, column, value)

    def set_cell(self, row, column, text):
        if isinstance(column, str):
            column = self.table.column_of(column)
        if not 0 <= row < self.table.rowCount():
            return
        item = self.table.item(row, column)
        if item is None:
            item = QTableWidgetItem()
            self.table.setItem(row, column, item)
        item.setText(str(text))
        item.setToolTip(str(text))

    def set_status(self, row, text):
        self.set_cell(row, "status", text)

    # ---- 删除 ----

    def delete_selected(self):
        rows = self.selected_indices()
        if self._busy or not rows:
            return
        for row in reversed(rows):
            self.table.removeRow(row)
            if row < len(self.rows):
                del self.rows[row]
        self._notify(f"已删除 {len(rows)} 项")

    def clear_all(self, notify=True):
        self.rows.clear()
        self.table.setRowCount(0)
        if notify:
            self._notify("已清空全部列表")

    # ---- 状态 ----

    def set_busy(self, busy):
        """任务执行期间禁用操作按钮，避免并发改动列表。"""
        self._busy = bool(busy)
        self._refresh()

    def _primary_ready(self, count):
        return count > 0

    def _primary_label(self, count):
        return f"{self._primary_text} ({count})" if count else self._primary_text

    def _refresh(self):
        total = self.table.rowCount()
        count = len(self.selected_indices())
        idle = not self._busy
        self.count_label.setText(f"已选 {count} / {total}")
        self.select_button.setEnabled(idle and total > 0)
        self.delete_button.setEnabled(idle and count > 0)
        self.clear_button.setEnabled(idle and total > 0)
        set_button_text(self.primary_button, self._primary_label(count))
        self.primary_button.setEnabled(idle and self._primary_ready(count))
        self.table.horizontalHeader().viewport().update()

    def _notify(self, text):
        if self.status_label is not None:
            self.status_label.setText(text)
