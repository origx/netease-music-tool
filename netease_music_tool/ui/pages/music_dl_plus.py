import threading
import tkinter as tk
from tkinter import filedialog

import ttkbootstrap as ttk

import netease_music_tool.config as config
from netease_music_tool.services.mdl_plus_service import download_plus_audio, fetch_plus_song_info
from netease_music_tool.services.music_service import parse_song_ids
from netease_music_tool.ui.components.mode_input import ModeInputFrame
from netease_music_tool.ui.components.song_list import SongListFrame


def build_page(parent, app, status_label):
    page = ttk.Frame(parent)
    save_path = tk.StringVar(value=config.DESKTOP_PATH)

    ttk.Label(page, text="MusicDawnloader(Plus)", font=(config.FONT_FAMILY, 16, "bold")).pack(anchor=tk.W, pady=(0, 12))
    ttk.Label(page, text="支持更高级的设置,可下载试听/完整音频", font=(config.FONT_FAMILY, 9), foreground=config.TEXT_HINT).pack(anchor=tk.W, pady=(0, 12))
    ttk.Label(
        page,
        text="因为平台对 Cookie 爬虫监管逐渐增强，不建议在 Cookie 模式下批量使用此功能",
        font=(config.FONT_FAMILY, 9),
        foreground="#F32D2D",
    ).pack(anchor=tk.W, pady=(0, 20))

    path = ttk.Frame(page)
    path.pack(fill=tk.X, pady=(0, 12))
    ttk.Label(path, text="保存目录: ", font=(config.FONT_FAMILY, 10)).pack(side=tk.LEFT)
    ttk.Entry(path, textvariable=save_path, font=(config.FONT_FAMILY, 10)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    ttk.Button(path, text="选择目录", bootstyle="secondary", command=lambda: choose_folder()).pack(side=tk.LEFT)

    mode_input = ModeInputFrame(page, on_mode_change=lambda enabled: on_mode_change(enabled))
    mode_input.pack(fill=tk.X)
    song_list = SongListFrame(
        page,
        status_label=status_label,
        on_fetch=lambda: fetch_info(),
        on_download=lambda: download_selected(),
    )
    song_list.pack(fill=tk.BOTH, expand=True)

    def choose_folder():
        folder = filedialog.askdirectory(title="选择下载保存文件夹")
        if folder:
            save_path.set(folder)

    def on_mode_change(enabled):
        song_list.set_single_mode(enabled)
        if enabled:
            song_list.clear_all(notify=False)

    def format_row(info):
        status = "可下载" if info.get("ok") else f"获取失败 ({info.get('error_code', '-')})"
        return (info.get("id", "-"), info.get("size_text", "-"), status)

    def fetch_info():
        raw_input = mode_input.get_input_text()
        ids = parse_song_ids(raw_input)
        if mode_input.is_cookie_mode() and len(ids) != 1:
            status_label.configure(text="Cookie 模式只能输入一个歌曲 ID")
            return
        if not ids:
            status_label.configure(text="请输入歌曲 ID 或链接")
            return
        song_list.fetch_button.configure(state=tk.DISABLED)
        status_label.configure(text=f"开始获取 {len(ids)} 首歌曲信息...")

        def request():
            try:
                result = fetch_plus_song_info(ids, mode_input.get_cookie())
            except Exception as exc:
                result = [{"id": ids[0], "ok": False, "url": None, "size": 0, "error": str(exc)}]
            app.after(0, lambda: show_results(result))

        threading.Thread(target=request, daemon=True).start()

    def show_results(result):
        song_list.populate(result, format_row)
        song_list.fetch_button.configure(state=tk.NORMAL)
        status_label.configure(text="歌曲信息获取完成")

    def download_selected():
        if mode_input.is_cookie_mode():
            indices = list(range(len(song_list.rows)))
        else:
            indices = song_list.selected_indices()
        if not indices:
            status_label.configure(text="请先选择要下载的歌曲")
            return
        targets = [(song_list.tree.get_children()[idx], song_list.rows[idx]) for idx in indices]
        for iid, info in targets:
            ok = download_plus_audio(
                info,
                save_path.get(),
                mode_input.get_cookie(),
                lambda text: status_label.configure(text=text),
            )
            song_list.set_status(iid, "下载完成" if ok else "下载失败")
        status_label.configure(text="下载任务结束")

    return page
