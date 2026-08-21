import threading
import tkinter as tk
from tkinter import filedialog

import ttkbootstrap as ttk

import netease_music_tool.config as config
from netease_music_tool.services.music_service import download_audio_by_info, fetch_song_info, parse_song_ids
from netease_music_tool.ui.components.song_list import SongListFrame


def build_page(parent, app, status_label):
    page = ttk.Frame(parent)
    save_path = tk.StringVar(value=config.DESKTOP_PATH)

    ttk.Label(page, text="MusicDawnloader(Basic)", font=(config.FONT_FAMILY, 16, "bold")).pack(anchor=tk.W, pady=(0, 12))
    ttk.Label(page, text="利用旧版官方API下载, 只能下载非VIP播放歌曲(30s都不行)", font=(config.FONT_FAMILY, 9), foreground=config.TEXT_HINT).pack(anchor=tk.W, pady=(0, 20))

    path = ttk.Frame(page)
    path.pack(fill=tk.X, pady=(0, 15))
    ttk.Label(path, text="保存目录: ", font=(config.FONT_FAMILY, 10)).pack(side=tk.LEFT)
    ttk.Entry(path, textvariable=save_path, font=(config.FONT_FAMILY, 10)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    ttk.Button(path, text="选择目录", bootstyle="secondary", command=lambda: choose()).pack(side=tk.LEFT)

    ttk.Label(page, text="ID/链接列表", font=(config.FONT_FAMILY, 10)).pack(anchor=tk.W)
    text = tk.Text(
        page,
        height=6,
        font=(config.FONT_FAMILY, 10),
        bg=config.BG_INPUT,
        fg=config.TEXT_NORMAL,
        insertbackground=config.TEXT_WHITE,
        relief="flat",
    )
    text.pack(fill=tk.X, pady=(8, 12))

    song_list = SongListFrame(
        page,
        status_label=status_label,
        on_fetch=lambda: fetch_info(),
        on_download=lambda: download_selected(),
    )
    song_list.pack(fill=tk.BOTH, expand=True)

    def choose():
        folder = filedialog.askdirectory(title="选择下载保存文件夹")
        if folder:
            save_path.set(folder)

    def format_row(info):
        return (
            info.get("id", "-"),
            info.get("size_text", "-"),
            "可下载" if info.get("ok") else "获取失败",
        )

    def fetch_info():
        ids = parse_song_ids(text.get("1.0", tk.END))
        if not ids:
            status_label.configure(text="请输入歌曲 ID 或链接")
            return
        song_list.fetch_button.configure(state=tk.DISABLED)
        status_label.configure(text="正在获取歌曲信息...")

        def request():
            result = fetch_song_info(ids)
            app.after(0, lambda: show(result))

        threading.Thread(target=request, daemon=True).start()

    def show(result):
        song_list.populate(result, format_row)
        song_list.fetch_button.configure(state=tk.NORMAL)
        status_label.configure(text="歌曲信息获取完成")

    def download_selected():
        indices = song_list.selected_indices()
        if not indices:
            status_label.configure(text="请先选择要下载的歌曲")
            return
        targets = [(song_list.tree.get_children()[idx], song_list.rows[idx]) for idx in indices]
        for iid, info in targets:
            ok = download_audio_by_info(info, save_path.get(), lambda text: status_label.configure(text=text))
            song_list.set_status(iid, "下载完成" if ok else "下载失败")
        status_label.configure(text="下载任务结束")

    return page
