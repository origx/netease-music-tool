"""Cookie 模式切换 + 批量/单行输入切换组件。

无 Cookie 时提供多行批量输入框（tk.Text），开启 Cookie 模式后切换为
单行输入框（ttk.Entry）。MDL(Plus) 与 MVDL 页面共用。
"""

import tkinter as tk

import ttkbootstrap as ttk

import netease_music_tool.config as config


class ModeInputFrame(ttk.Frame):
    def __init__(
        self,
        parent,
        on_mode_change=None,
        label_batch="ID/链接列表",
        label_single="ID",
        hint_batch="无 Cookie 时可批量输入，一行一个",
        hint_single="Cookie 模式只能输入一个 ID，先获取信息再下载",
    ):
        super().__init__(parent)
        self._on_mode_change = on_mode_change
        self.cookie_enabled = tk.BooleanVar(value=False)
        self.cookie = tk.StringVar()

        mode_row = ttk.Frame(self)
        mode_row.pack(fill=tk.X, pady=(0, 12))
        ttk.Checkbutton(
            mode_row,
            text="是否使用 Cookie",
            variable=self.cookie_enabled,
            bootstyle="round-toggle",
            command=self._update_mode,
        ).pack(side=tk.LEFT, padx=12)

        self.cookie_frame = ttk.Frame(self)
        self.cookie_entry = ttk.Entry(self.cookie_frame, textvariable=self.cookie, show="*")
        self.cookie_entry.pack(fill=tk.X, expand=True)

        self.label = ttk.Label(self, text=label_batch, font=(config.FONT_FAMILY, 10))
        self.label.pack(anchor=tk.W)
        self.hint = ttk.Label(self, text=hint_batch, font=(config.FONT_FAMILY, 9), foreground=config.TEXT_HINT)
        self.hint.pack(anchor=tk.W, pady=(8, 5))

        self.batch_text = tk.Text(
            self,
            height=6,
            font=(config.FONT_FAMILY, 10),
            bg=config.BG_INPUT,
            fg=config.TEXT_NORMAL,
            insertbackground=config.TEXT_WHITE,
            relief="flat",
        )
        self.single_input = ttk.Entry(self, font=(config.FONT_FAMILY, 10))
        self.batch_text.pack(fill=tk.X, pady=(0, 12))

        self._hints = (label_batch, hint_batch, label_single, hint_single)
        self._update_mode(notify=False)

    def _update_mode(self, notify=True):
        enabled = self.cookie_enabled.get()
        label_batch, hint_batch, label_single, hint_single = self._hints
        if enabled:
            self.cookie_frame.pack(fill=tk.X, pady=(0, 12), before=self.label)
            self.cookie_entry.configure(state=tk.NORMAL)
            self.batch_text.pack_forget()
            self.single_input.pack(fill=tk.X, pady=(0, 12))
            self.single_input.delete(0, tk.END)
            self.label.configure(text=label_single)
            self.hint.configure(text=hint_single)
        else:
            self.cookie_frame.pack_forget()
            self.single_input.pack_forget()
            self.batch_text.pack(fill=tk.X, pady=(0, 12))
            self.batch_text.delete("1.0", tk.END)
            self.label.configure(text=label_batch)
            self.hint.configure(text=hint_batch)
        if notify and self._on_mode_change:
            self._on_mode_change(enabled)

    def is_cookie_mode(self):
        return self.cookie_enabled.get()

    def get_input_text(self):
        if self.cookie_enabled.get():
            return self.single_input.get()
        return self.batch_text.get("1.0", tk.END)

    def get_cookie(self):
        return self.cookie.get() if self.cookie_enabled.get() else ""
