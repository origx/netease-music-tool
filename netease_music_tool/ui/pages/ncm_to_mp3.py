import os
import threading
import tkinter as tk
from tkinter import filedialog

import ttkbootstrap as ttk

import netease_music_tool.config as config
from netease_music_tool.services.music_service import decrypt_ncm, read_ncm_metadata
from netease_music_tool.ui.components.convert_list import ConvertListFrame


def build_page(parent, app, status_label):
    page = ttk.Frame(parent)
    output_dir = tk.StringVar(value=config.DESKTOP_PATH)

    ttk.Label(page, text="NCM to MP3/FLAC", font=(config.FONT_FAMILY, 16, "bold")).pack(anchor=tk.W, pady=(0, 12))
    ttk.Label(page, text="选择一个或多个 .ncm 文件，转换为标准音频格式", font=(config.FONT_FAMILY, 9), foreground=config.TEXT_HINT).pack(anchor=tk.W, pady=(0, 20))

    path = ttk.Frame(page)
    path.pack(fill=tk.X, pady=(0, 15))
    ttk.Label(path, text="保存目录: ", font=(config.FONT_FAMILY, 10)).pack(side=tk.LEFT)
    ttk.Entry(path, textvariable=output_dir, font=(config.FONT_FAMILY, 10)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    ttk.Button(path, text="选择目录", bootstyle="secondary", command=lambda: choose()).pack(side=tk.LEFT)

    embed_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(
        page,
        text="打包元数据/封面到歌曲文件",
        variable=embed_var,
        bootstyle="round-toggle",
    ).pack(anchor=tk.W, pady=(0, 10))

    convert_list = ConvertListFrame(
        page,
        status_label=status_label,
        on_add=lambda: add_files(),
        on_convert=lambda: convert_files(),
    )
    convert_list.pack(fill=tk.BOTH, expand=True)

    def choose():
        folder = filedialog.askdirectory(title="选择转换保存文件夹")
        if folder:
            output_dir.set(folder)

    def add_files():
        added = 0
        for file_path in filedialog.askopenfilenames(title="选择 NCM 文件", filetypes=[("NCM 文件", "*.ncm")]):
            if any(record.get("path") == file_path for record in convert_list.rows):
                continue
            try:
                metadata = read_ncm_metadata(file_path)
            except Exception as exc:
                status_label.configure(text=f"读取失败: {exc}")
                continue
            convert_list.add_row({**metadata, "path": file_path})
            added += 1
        status_label.configure(text=f"已添加 {added} 个 NCM 文件")

    def convert_files():
        targets = [
            (iid, convert_list.rows[convert_list.tree.index(iid)])
            for iid in convert_list.tree.selection()
        ]
        if not targets:
            status_label.configure(text="请先选择要转换的文件")
            return
        os.makedirs(output_dir.get(), exist_ok=True)
        convert_list.convert_button.configure(state=tk.DISABLED)

        def work():
            success = 0
            for iid, record in targets:
                app.after(0, lambda item=iid: convert_list.set_status(item, "转换中"))
                try:
                    out_path = decrypt_ncm(record["path"], output_dir.get(), embed_metadata=bool(embed_var.get()))
                    size_text = f"{os.path.getsize(out_path) / 1024 / 1024:.2f} MB"
                    success += 1
                    state, size_val = "转换完成", size_text
                except Exception as exc:
                    state, size_val = f"失败: {exc}", "-"
                app.after(0, lambda item=iid, s=state, sz=size_val: (
                    convert_list.set_status(item, s),
                    convert_list.set_size(item, sz),
                ))
            app.after(0, lambda: (
                convert_list.convert_button.configure(state=tk.NORMAL),
                status_label.configure(text=f"转换完成，成功 {success} 个"),
            ))

        threading.Thread(target=work, daemon=True).start()

    return page
