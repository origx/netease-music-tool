import tkinter as tk

import ttkbootstrap as ttk


def create_nav_item(parent, text, command, active=False):
    style_name = "NavActive.TLabel" if active else "Nav.TLabel"
    label = ttk.Label(parent, text=text, style=style_name, cursor="hand2")
    label.pack(fill=tk.X)
    label.bind("<Button-1>", lambda event: command())
    return label