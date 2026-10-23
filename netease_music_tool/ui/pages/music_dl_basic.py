"""MDL(Basic) 页面：通过旧版官方 API 下载非 VIP 播放歌曲。"""

import netease_music_tool.config as config
from netease_music_tool.services.music_service import (
    download_audio_by_info,
    fetch_song_info,
    parse_song_ids,
)
from netease_music_tool.ui.components.common import PageHeader, PathPicker
from netease_music_tool.ui.components.mode_input import ModeInputWidget
from netease_music_tool.ui.components.song_list import SongListWidget
from netease_music_tool.ui.pages.base import StatusPage


class MusicDlBasicPage(StatusPage):
    def __init__(self, status_label, parent=None):
        super().__init__(status_label, parent)
        layout = self.page_layout

        layout.addWidget(
            PageHeader(
                "MusicDownloader(Basic)",
                "利用旧版官方 API 下载，只能下载非 VIP 播放歌曲（30s 试听也不行）",
            )
        )

        self.mode_input = ModeInputWidget(
            label_batch="ID/链接列表",
            hint_batch="一行一个歌曲 ID 或网页链接",
            allow_cookie=False,
        )
        self.mode_input.fetchRequested.connect(self.fetch_info)
        layout.addWidget(self.mode_input)

        self.song_list = SongListWidget(status_label=status_label)
        self.song_list.downloadRequested.connect(self.download_selected)
        self.path_picker = PathPicker("选择下载保存文件夹", config.DESKTOP_PATH)
        self.song_list.add_footer_widget(self.path_picker, 1)
        self.list_widget = self.song_list
        self.busy_widgets = (self.mode_input, self.song_list)
        layout.addWidget(self.song_list, 1)

    @staticmethod
    def _format_row(info):
        return (
            info.get("id", "-"),
            info.get("size_text", "-"),
            "可下载" if info.get("ok") else "获取失败",
        )

    def fetch_info(self):
        ids = parse_song_ids(self.mode_input.get_input_text())
        if not ids:
            self.set_status("请输入歌曲 ID 或链接")
            return
        self.set_busy(True)
        self.set_status("正在获取歌曲信息...")
        self.runner.submit(
            fetch_song_info,
            ids,
            on_done=self._on_fetched,
            on_error=self._on_fetch_error,
        )

    def _on_fetched(self, result):
        self.song_list.populate(result, self._format_row)
        self.set_busy(False)
        self.set_status("歌曲信息获取完成，已自动勾选可下载项")

    def _on_fetch_error(self, message):
        self.set_busy(False)
        self.set_status(f"获取歌曲信息失败: {message}")

    def download_selected(self):
        indices = self.song_list.selected_indices()
        if not indices:
            self.set_status("请先选择要下载的歌曲")
            return
        targets = [(row, self.song_list.rows[row]) for row in indices]
        save_dir = self.path_picker.path()
        self.set_busy(True)
        self.start_download(
            targets,
            lambda info: download_audio_by_info(info, save_dir),
            lambda info: f"正在下载 ID:{info.get('id')}",
            on_done=self._on_download_done,
            on_error=self._on_download_error,
        )

    def _on_download_done(self, success):
        self.set_busy(False)
        self.set_status(f"下载任务结束，成功 {success} 首")

    def _on_download_error(self, message):
        self.set_busy(False)
        self.set_status(f"下载失败: {message}")


def build_page(parent, status_label):
    return MusicDlBasicPage(status_label, parent)
