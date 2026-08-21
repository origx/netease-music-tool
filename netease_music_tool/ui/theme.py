import ttkbootstrap as ttk
from tkinter import font
from ttkbootstrap.constants import *
import netease_music_tool.config as config

from netease_music_tool.config import (
    BG_DARK,
    BG_HOVER,
    BG_INPUT,
    BG_PANEL,
    BORDER,
    FONT_FAMILIES,
    PRIMARY_BLUE,
    PRIMARY_HOVER,
    SELECT_BG,
    SELECT_FG,
    STRIPE_BG,
    TEXT_NORMAL,
    TEXT_WHITE,
    TEXT_HINT,
)


def configure_application_theme():
    installed_fonts = set(font.families())
    selected_font = next((family for family in FONT_FAMILIES if family in installed_fonts), None)
    default_font = font.nametofont("TkDefaultFont")
    if selected_font:
        default_font.configure(family=selected_font)
    selected_font = selected_font or default_font.cget("family")
    default_font.configure(size=13)

    style = ttk.Style()
    style.configure('.', font=(selected_font, 9), background=BG_DARK, foreground=TEXT_NORMAL)

    style.configure('Nav.TLabel',
                    background=BG_PANEL,
                    foreground=TEXT_NORMAL,
                    padding=(15, 12),
                    anchor='w',
                    font=(selected_font, 10))
    style.map('Nav.TLabel',
              background=[('active', BG_HOVER)],
              foreground=[('active', TEXT_WHITE)])

    style.configure('NavActive.TLabel',
                    background=PRIMARY_BLUE,
                    foreground=TEXT_WHITE,
                    padding=(15, 12),
                    anchor='w',
                    font=(selected_font, 10))
    style.map('NavActive.TLabel',
              background=[('active', PRIMARY_HOVER)])

    style.configure("Treeview",
                    background=BG_INPUT,
                    foreground=TEXT_NORMAL,
                    fieldbackground=BG_INPUT,
                    borderwidth=0,
                    rowheight=40,
                    font=(selected_font, 10))
    style.map("Treeview",
              background=[('selected', SELECT_BG)],
              foreground=[('selected', SELECT_FG)])

    style.configure("Song.TCheckbutton",
                    background=BG_INPUT,
                    foreground=TEXT_NORMAL,
                    padding=2)
    style.map("Song.TCheckbutton",
              background=[('active', BG_HOVER)],
              foreground=[('disabled', TEXT_HINT)])

    style.configure("Treeview.Heading",
                    background=BG_PANEL,
                    foreground=TEXT_NORMAL,
                    relief="flat",
                    borderwidth=0,
                    padding=(5, 8),
                    font=(selected_font, 10, 'bold'))
    style.map("Treeview.Heading",
              background=[('active', BG_HOVER)],
              foreground=[('active', TEXT_WHITE)])

    style.configure("TEntry",
                    fieldbackground=BG_INPUT,
                    foreground=TEXT_NORMAL,
                    insertcolor=TEXT_WHITE,
                    bordercolor=BORDER,
                    lightcolor=BORDER,
                    darkcolor=BORDER)
    style.map("TEntry",
              bordercolor=[('focus', PRIMARY_BLUE)],
              lightcolor=[('focus', PRIMARY_BLUE)],
              darkcolor=[('focus', PRIMARY_BLUE)])

    style.configure("TButton",
                    font=(selected_font, 10),
                    padding=(15, 8),
                    borderwidth=0)

    # 只覆盖 ttkbootstrap 的主题按钮变体，避免和默认主题风格冲突.
    style.configure("primary.TButton",
                    background=PRIMARY_BLUE,
                    foreground=TEXT_WHITE,
                    borderwidth=0)
    style.map("primary.TButton",
              background=[('active', PRIMARY_HOVER), ('pressed', PRIMARY_BLUE)],
              foreground=[('active', TEXT_WHITE), ('pressed', TEXT_WHITE)])

    style.configure("secondary.TButton",
                    background=BG_PANEL,
                    foreground=TEXT_NORMAL,
                    borderwidth=0)
    style.map("secondary.TButton",
              background=[('active', BG_HOVER), ('pressed', BG_PANEL)],
              foreground=[('active', TEXT_WHITE), ('pressed', TEXT_NORMAL)])

    style.configure("Status.TLabel",
                    background=BG_PANEL,
                    foreground=TEXT_NORMAL,
                    padding=(10, 5),
                    font=(selected_font, 9))

    config.FONT_FAMILY = selected_font
    return style
