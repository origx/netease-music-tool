from PySide6.QtWidgets import QVBoxLayout, QWidget

from netease_music_tool.ui.workers import TaskRunner


class StatusPage(QWidget):
    def __init__(self, status_label, parent=None):
        super().__init__(parent)
        self.status_label = status_label
        self.runner = TaskRunner(self)
        self.list_widget = None
        self.busy_widgets = ()
        self.page_layout = QVBoxLayout(self)
        self.page_layout.setContentsMargins(0, 0, 0, 0)
        self.page_layout.setSpacing(12)

    def set_status(self, text):
        if self.status_label is not None:
            self.status_label.setText(text)

    def set_busy(self, busy):
        """任务执行期间锁定输入区与列表操作。"""
        for widget in self.busy_widgets:
            widget.set_busy(busy)

    def apply_progress(self, event):
        """进度事件：("status", 文案) / ("row", 行号, 文案) / ("size", 行号, 文案)。"""
        kind, *payload = event
        if kind == "status":
            self.set_status(payload[0])
        elif kind == "row" and self.list_widget is not None:
            self.list_widget.set_status(payload[0], payload[1])
        elif kind == "size" and self.list_widget is not None:
            self.list_widget.set_size(payload[0], payload[1])

    def start_download(self, targets, download_fn, describe, on_done, on_error):
        """在后台逐条下载并回写列表状态。

        targets: [(行号, info)]；download_fn(info) -> bool；describe(info) -> 状态栏文案。
        """

        def task(progress=None):
            success = 0
            for row, info in targets:
                progress(("status", describe(info)))
                progress(("row", row, "下载中"))
                ok = download_fn(info)
                success += 1 if ok else 0
                progress(("row", row, "下载完成" if ok else "下载失败"))
            return success

        self.runner.submit(task, on_done=on_done, on_error=on_error, on_progress=self.apply_progress)
