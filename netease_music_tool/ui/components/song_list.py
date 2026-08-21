"""多选下载列表组件。

MDL(Basic)、MDL(Plus)、MVDL 页面共用。支持多选、删除选中、下载选中、
全部删除；开启 Cookie 单曲模式时只保留「获取信息 / 下载」两个按钮。
"""

import tkinter as tk

import ttkbootstrap as ttk


class SongListFrame(ttk.Frame):
    def __init__(
        self,
        parent,
        status_label=None,
        on_fetch=None,
        on_download=None,
        fetch_text="获取信息",
        download_text="下载选中项",
        columns=(("id", "歌曲 ID", 260), ("size", "文件大小", 160), ("status", "状态", 260)),
        single_mode=False,
    ):
        super().__init__(parent)
        self.status_label = status_label
        self._on_fetch = on_fetch
        self._on_download = on_download
        self.rows = []
        self._single_mode = single_mode

        action = ttk.Frame(self)
        action.pack(fill=tk.X, pady=(0, 12))
        self.fetch_button = ttk.Button(action, text=fetch_text, bootstyle="primary", command=on_fetch)
        self.select_all_button = ttk.Button(action, text="全选", bootstyle="secondary", command=self.select_all)
        self.download_button = ttk.Button(action, text=download_text, bootstyle="primary", command=on_download)
        self.delete_button = ttk.Button(action, text="删除选中", bootstyle="secondary", command=self.delete_selected)
        self.clear_button = ttk.Button(action, text="全部删除", bootstyle="secondary", command=self.clear_all)

        self.tree = ttk.Treeview(
            self,
            columns=[column[0] for column in columns],
            show="headings",
            selectmode="extended",
            height=10,
        )
        for column, title, width in columns:
            self.tree.heading(column, text=title)
            self.tree.column(column, width=width, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self._apply_mode()

    def set_single_mode(self, single):
        self._single_mode = single
        self._apply_mode()

    def _apply_mode(self):
        if self._single_mode:
            self.fetch_button.pack(side=tk.LEFT, padx=(0, 10))
            self.download_button.pack(side=tk.LEFT)
            self.download_button.configure(text="下载")
            self.select_all_button.pack_forget()
            self.delete_button.pack_forget()
            self.clear_button.pack_forget()
        else:
            self.fetch_button.pack(side=tk.LEFT, padx=(0, 10))
            self.select_all_button.pack(side=tk.LEFT, padx=(0, 10))
            self.download_button.pack(side=tk.LEFT, padx=(0, 10))
            self.download_button.configure(text="下载选中项")
            self.delete_button.pack(side=tk.LEFT, padx=(0, 10))
            self.clear_button.pack(side=tk.LEFT)

    def populate(self, infos, format_row):
        """用条目列表重建表格。format_row(info) 返回一行的值元组。"""
        self.rows = list(infos)
        self.tree.delete(*self.tree.get_children())
        for info in infos:
            self.tree.insert("", tk.END, values=format_row(info))

    def selected_indices(self):
        return [self.tree.index(iid) for iid in self.tree.selection()]

    def select_all(self):
        self.tree.selection_set(self.tree.get_children())

    def set_status(self, iid, text):
        self.tree.set(iid, "status", text)

    def delete_selected(self):
        indices = sorted((self.tree.index(iid) for iid in self.tree.selection()), reverse=True)
        for idx in indices:
            if idx < len(self.rows):
                del self.rows[idx]
            self.tree.delete(self.tree.get_children()[idx])
        if self.status_label:
            self.status_label.configure(text="已删除选中")

    def clear_all(self, notify=True):
        self.rows.clear()
        self.tree.delete(*self.tree.get_children())
        if notify and self.status_label:
            self.status_label.configure(text="已清空全部列表")
