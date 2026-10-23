"""MVDL 页面：网易云音乐 MV 下载。"""

import netease_music_tool.config as config
from netease_music_tool.services.music_service import download_mv, fetch_mv_info, parse_song_ids
from netease_music_tool.ui.components.common import PageHeader, PathPicker
from netease_music_tool.ui.components.mode_input import ModeInputWidget
from netease_music_tool.ui.components.song_list import SongListWidget
from netease_music_tool.ui.pages.base import StatusPage

MV_COLUMNS = (
    ("id", "MV ID", 160),
    ("name", "MV 名称", None),
    ("status", "状态", 170),
)


class MvDownloadPage(StatusPage):
    def __init__(self, status_label, parent=None):
        super().__init__(status_label, parent)
        layout = self.page_layout

        layout.addWidget(
            PageHeader(
                "MV Downloader",
                "网易云音乐视频下载工具",
                "因为平台对 Cookie 爬虫监管逐渐增强，不建议在 Cookie 模式下批量使用此功能",
            )
        )

        self.mode_input = ModeInputWidget(
            label_batch="MV ID/链接列表",
            label_single="MV ID",
            hint_batch="无 Cookie 时可批量输入，一行一个",
            hint_single="Cookie 模式只能输入一个 MV ID",
        )
        self.mode_input.modeChanged.connect(self._on_mode_change)
        self.mode_input.fetchRequested.connect(self.fetch_info)
        layout.addWidget(self.mode_input)

        self.song_list = SongListWidget(
            status_label=status_label,
            columns=MV_COLUMNS,
            title="MV 列表",
            empty_text="输入 MV ID 或链接后点击「获取信息」",
        )
        self.song_list.downloadRequested.connect(self.download_selected)
        self.path_picker = PathPicker("选择视频保存目录", config.DESKTOP_PATH)
        self.song_list.add_footer_widget(self.path_picker, 1)
        self.list_widget = self.song_list
        self.busy_widgets = (self.mode_input, self.song_list)
        layout.addWidget(self.song_list, 1)

    @staticmethod
    def _format_row(info):
        return (
            info.get("id", "-"),
            info.get("name", "-"),
            "可下载" if info.get("ok") else "获取失败",
        )

    def _on_mode_change(self, enabled):
        self.song_list.set_single_mode(enabled)
        if enabled:
            self.song_list.clear_all(notify=False)

    def fetch_info(self):
        ids = parse_song_ids(self.mode_input.get_input_text())
        if self.mode_input.is_cookie_mode() and len(ids) != 1:
            self.set_status("Cookie 模式只能输入一个 MV ID")
            return
        if not ids:
            self.set_status("请输入 MV ID 或链接")
            return
        self.set_busy(True)
        self.set_status(f"正在获取 {len(ids)} 个 MV 信息...")
        self.runner.submit(
            fetch_mv_info,
            ids,
            self.mode_input.get_cookie(),
            on_done=self._on_fetched,
            on_error=self._on_fetch_error,
        )

    def _on_fetched(self, result):
        self.song_list.populate(result, self._format_row)
        self.set_busy(False)
        self.set_status("MV 信息获取完成")

    def _on_fetch_error(self, message):
        self.set_busy(False)
        self.set_status(f"获取 MV 信息失败: {message}")

    def download_selected(self):
        if self.mode_input.is_cookie_mode():
            indices = list(range(len(self.song_list.rows)))
        else:
            indices = self.song_list.selected_indices()
        if not indices:
            self.set_status("请先选择要下载的 MV")
            return
        targets = [(row, self.song_list.rows[row]) for row in indices]
        save_dir = self.path_picker.path()
        self.set_busy(True)
        self.start_download(
            targets,
            lambda info: download_mv(info, save_dir),
            lambda info: f"正在下载 MV:{info.get('id')} {info.get('name', '')}".strip(),
            on_done=self._on_download_done,
            on_error=self._on_download_error,
        )

    def _on_download_done(self, success):
        self.set_busy(False)
        self.set_status(f"下载任务结束，成功 {success} 个")

    def _on_download_error(self, message):
        self.set_busy(False)
        self.set_status(f"下载失败: {message}")


def build_page(parent, status_label):
    return MvDownloadPage(status_label, parent)
