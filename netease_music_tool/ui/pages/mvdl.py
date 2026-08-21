import threading
import tkinter as tk
from tkinter import filedialog

import ttkbootstrap as ttk

import netease_music_tool.config as config
from netease_music_tool.services.music_service import download_mv, fetch_mv_info, parse_song_ids
from netease_music_tool.ui.components.mode_input import ModeInputFrame
from netease_music_tool.ui.components.song_list import SongListFrame


def build_page(parent, app, status_label):
    page = ttk.Frame(parent)
    save_path = tk.StringVar(value=config.DESKTOP_PATH)

    ttk.Label(page, text="MV Dawnloader", font=(config.FONT_FAMILY, 16, "bold")).pack(anchor=tk.W, pady=(0, 12))
    ttk.Label(page, text="网易云音乐视频下载工具", font=(config.FONT_FAMILY, 9), foreground=config.TEXT_HINT).pack(anchor=tk.W, pady=(0, 12))
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
    ttk.Button(path, text="选择目录", bootstyle="secondary", command=lambda: choose()).pack(side=tk.LEFT)

    mode_input = ModeInputFrame(
        page,
        on_mode_change=lambda enabled: on_mode_change(enabled),
        label_batch="MV ID/链接列表",
        label_single="MV ID",
        hint_batch="无 Cookie 时可批量输入，一行一个",
        hint_single="Cookie 模式只能输入一个 MV ID，先获取信息再下载",
    )
    mode_input.pack(fill=tk.X)
    song_list = SongListFrame(
        page,
        status_label=status_label,
        on_fetch=lambda: fetch_info(),
        on_download=lambda: download_selected(),
        columns=(("id", "MV ID", 200), ("name", "MV 名称", 280), ("status", "状态", 200)),
    )
    song_list.pack(fill=tk.BOTH, expand=True)

    def choose():
        folder = filedialog.askdirectory(title="选择视频保存目录")
        if folder:
            save_path.set(folder)

    def on_mode_change(enabled):
        song_list.set_single_mode(enabled)
        if enabled:
            song_list.clear_all(notify=False)

    def format_row(info):
        return (
            info.get("id", "-"),
            info.get("name", "-"),
            "可下载" if info.get("ok") else "获取失败",
        )

    def fetch_info():
        ids = parse_song_ids(mode_input.get_input_text())
        if mode_input.is_cookie_mode() and len(ids) != 1:
            status_label.configure(text="Cookie 模式只能输入一个 MV ID")
            return
        if not ids:
            status_label.configure(text="请输入 MV ID 或链接")
            return
        song_list.fetch_button.configure(state=tk.DISABLED)
        status_label.configure(text=f"正在获取 {len(ids)} 个 MV 信息...")

        def request():
            result = fetch_mv_info(ids, mode_input.get_cookie())
            app.after(0, lambda: show(result))

        threading.Thread(target=request, daemon=True).start()

    def show(result):
        song_list.populate(result, format_row)
        song_list.fetch_button.configure(state=tk.NORMAL)
        status_label.configure(text="MV 信息获取完成")

    def download_selected():
        if mode_input.is_cookie_mode():
            indices = list(range(len(song_list.rows)))
        else:
            indices = song_list.selected_indices()
        if not indices:
            status_label.configure(text="请先选择要下载的 MV")
            return
        targets = [(song_list.tree.get_children()[idx], song_list.rows[idx]) for idx in indices]
        for iid, info in targets:
            ok = download_mv(info, save_path.get(), lambda text: status_label.configure(text=text))
            song_list.set_status(iid, "下载完成" if ok else "下载失败")
        status_label.configure(text="下载任务结束")

    return page
