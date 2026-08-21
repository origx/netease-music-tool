"""NCM 转换列表组件。

NCM2MP3 页面使用。显示封面缩略图（放大）、歌名、歌手、时长、转换大小、
状态；支持多选、删除选中、全部删除、转换选中项。
"""

import tkinter as tk
from io import BytesIO

from PIL import Image, ImageTk

import ttkbootstrap as ttk


class ConvertListFrame(ttk.Frame):
    COLUMNS = (
        ("title", "歌名", 200),
        ("artist", "歌手", 140),
        ("duration", "时长", 90),
        ("size", "转换大小", 100),
        ("status", "状态", 200),
    )

    def __init__(self, parent, status_label=None, on_add=None, on_convert=None, thumb_size=56):
        super().__init__(parent)
        self.status_label = status_label
        self._on_add = on_add
        self._on_convert = on_convert
        self.rows = []
        self._photos = []
        self._thumb_size = thumb_size

        action = ttk.Frame(self)
        action.pack(fill=tk.X, pady=(0, 12))
        self.add_button = ttk.Button(action, text="添加文件", bootstyle="primary", command=on_add)
        self.delete_button = ttk.Button(action, text="删除选中", bootstyle="secondary", command=self.delete_selected)
        self.clear_button = ttk.Button(action, text="全部删除", bootstyle="secondary", command=self.clear_all)
        self.convert_button = ttk.Button(action, text="转换选中项", bootstyle="primary", command=on_convert)

        style_name = f"ConvertList_{thumb_size}.Treeview"
        style = ttk.Style()
        style.configure(style_name, rowheight=thumb_size + 8)
        self.tree = ttk.Treeview(
            self,
            columns=[column[0] for column in self.COLUMNS],
            show="tree headings",
            selectmode="extended",
            height=10,
            style=style_name,
        )
        self.tree.heading("#0", text="封面")
        self.tree.column("#0", width=thumb_size + 30, minwidth=thumb_size + 30, anchor=tk.CENTER, stretch=False)
        for column, title, width in self.COLUMNS:
            self.tree.heading(column, text=title)
            self.tree.column(column, width=width, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.add_button.pack(side=tk.LEFT, padx=(0, 10))
        self.delete_button.pack(side=tk.LEFT, padx=(0, 10))
        self.clear_button.pack(side=tk.LEFT, padx=(0, 10))
        self.convert_button.pack(side=tk.LEFT)

    def add_row(self, record):
        """record: 含 title/artist/duration_text/size_text/cover(字节) 等字段。"""
        self.rows.append(record)
        photo = self._make_photo(record.get("cover")) if record.get("cover") else None
        self._photos.append(photo)
        self.tree.insert(
            "",
            tk.END,
            image=photo,
            values=(
                record.get("title", ""),
                record.get("artist", ""),
                record.get("duration_text", "00:00"),
                record.get("size_text", "-"),
                "待转换",
            ),
        )

    def _make_photo(self, data):
        try:
            image = Image.open(BytesIO(data)).convert("RGBA")
            image.thumbnail((self._thumb_size, self._thumb_size))
            return ImageTk.PhotoImage(image)
        except Exception:
            return None

    def selected_indices(self):
        return [self.tree.index(iid) for iid in self.tree.selection()]

    def set_status(self, iid, text):
        self.tree.set(iid, "status", text)

    def set_size(self, iid, text):
        self.tree.set(iid, "size", text)

    def delete_selected(self):
        indices = sorted((self.tree.index(iid) for iid in self.tree.selection()), reverse=True)
        for idx in indices:
            if idx < len(self.rows):
                del self.rows[idx]
            if idx < len(self._photos):
                del self._photos[idx]
            self.tree.delete(self.tree.get_children()[idx])
        if self.status_label:
            self.status_label.configure(text="已删除选中")

    def clear_all(self, notify=True):
        self.rows.clear()
        self._photos.clear()
        self.tree.delete(*self.tree.get_children())
        if notify and self.status_label:
            self.status_label.configure(text="已清空全部列表")
