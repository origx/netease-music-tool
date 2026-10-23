"""NCM2MP3 页面：解析 .ncm 文件并转换为标准音频格式。"""

import os

from PySide6.QtWidgets import QFileDialog

import netease_music_tool.config as config
from netease_music_tool.services.music_service import decrypt_ncm, read_ncm_metadata
from netease_music_tool.ui.components.common import CheckBox, PageHeader, PathPicker
from netease_music_tool.ui.components.convert_list import ConvertListWidget
from netease_music_tool.ui.pages.base import StatusPage


class NcmToMp3Page(StatusPage):
    def __init__(self, status_label, parent=None):
        super().__init__(status_label, parent)
        layout = self.page_layout

        layout.addWidget(
            PageHeader(
                "NCM to MP3/FLAC",
                "选择或拖入一个或多个 .ncm 文件，转换为标准音频格式",
            )
        )

        self.convert_list = ConvertListWidget(status_label=status_label)
        self.convert_list.addRequested.connect(self.add_files)
        self.convert_list.filesDropped.connect(self.add_paths)
        self.convert_list.convertRequested.connect(self.convert_files)
        self.embed_checkbox = CheckBox("嵌入元数据/封面")
        self.embed_checkbox.setToolTip("打包元数据/封面到歌曲文件")
        self.embed_checkbox.setChecked(True)
        self.convert_list.add_footer_widget(self.embed_checkbox)
        self.path_picker = PathPicker("选择转换保存文件夹", config.DESKTOP_PATH)
        self.convert_list.add_footer_widget(self.path_picker, 1)
        self.list_widget = self.convert_list
        self.busy_widgets = (self.convert_list,)
        layout.addWidget(self.convert_list, 1)

    def add_files(self):
        files, _selected_filter = QFileDialog.getOpenFileNames(
            self, "选择 NCM 文件", "", "NCM 文件 (*.ncm)"
        )
        self.add_paths(files)

    def add_paths(self, files):
        added = 0
        for file_path in files:
            if any(record.get("path") == file_path for record in self.convert_list.rows):
                continue
            try:
                metadata = read_ncm_metadata(file_path)
            except Exception as exc:  # noqa: BLE001 - 单个文件失败不影响其余文件
                self.set_status(f"读取失败: {exc}")
                continue
            self.convert_list.add_row({**metadata, "path": file_path})
            added += 1
        self.set_status(f"已添加 {added} 个 NCM 文件")

    def convert_files(self):
        targets = [
            (row, self.convert_list.rows[row])
            for row in self.convert_list.selected_indices()
        ]
        if not targets:
            self.set_status("请先选择要转换的文件")
            return

        output_dir = self.path_picker.path()
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as exc:
            self.set_status(f"无法创建保存目录: {exc}")
            return

        embed = self.embed_checkbox.isChecked()
        self.set_busy(True)

        def task(progress=None):
            success = 0
            for row, record in targets:
                progress(("row", row, "转换中"))
                try:
                    out_path = decrypt_ncm(record["path"], output_dir, embed_metadata=embed)
                except Exception as exc:  # noqa: BLE001 - 转换失败写回该行状态
                    progress(("row", row, f"失败: {exc}"))
                    continue
                size_text = f"{os.path.getsize(out_path) / 1024 / 1024:.2f} MB"
                progress(("row", row, "转换完成"))
                progress(("size", row, size_text))
                success += 1
            return success

        self.runner.submit(
            task,
            on_done=self._on_convert_done,
            on_error=self._on_convert_error,
            on_progress=self.apply_progress,
        )

    def _on_convert_done(self, success):
        self.set_busy(False)
        self.set_status(f"转换完成，成功 {success} 个")

    def _on_convert_error(self, message):
        self.set_busy(False)
        self.set_status(f"转换任务失败: {message}")


def build_page(parent, status_label):
    return NcmToMp3Page(status_label, parent)
