import tkinter as tk

import ttkbootstrap as ttk

from netease_music_tool.config import (
    APP_TITLE,
    FONT_FAMILY,
    WINDOW_MIN_SIZE,
    WINDOW_SIZE,
)
from netease_music_tool.ui.components.navigation import create_nav_item
from netease_music_tool.ui.pages.music_dl_basic import build_page as build_basic_page
from netease_music_tool.ui.pages.music_dl_plus import build_page as build_plus_page
from netease_music_tool.ui.pages.mvdl import build_page as build_mvdl_page
from netease_music_tool.ui.pages.ncm_to_mp3 import build_page as build_ncm_page
from netease_music_tool.ui.theme import configure_application_theme


def run_app():
    app = ttk.Window(
        themename="darkly",
        title=APP_TITLE,
        size=WINDOW_SIZE,
        resizable=(True, True),
        minsize=WINDOW_MIN_SIZE,
    )
    configure_application_theme()

    app.rowconfigure(0, weight=1)
    app.columnconfigure(0, weight=1)
    main_container = ttk.Frame(app)
    main_container.grid(row=0, column=0, sticky="nsew")

    sidebar = ttk.Frame(main_container, width=250)
    sidebar.pack(side=tk.LEFT, fill=tk.Y)
    sidebar.pack_propagate(False)
    ttk.Separator(sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=15, pady=(20, 10))
    nav_container = ttk.Frame(sidebar)
    nav_container.pack(fill=tk.X, pady=(10, 10))

    content_area = ttk.Frame(main_container)
    content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=24, pady=24)
    status_label = ttk.Label(app, text="就绪", style="Status.TLabel")
    status_label.grid(row=1, column=0, sticky="ew")

    pages = (
        build_basic_page(content_area, app, status_label),
        build_plus_page(content_area, app, status_label),
        build_ncm_page(content_area, app, status_label),
        build_mvdl_page(content_area, app, status_label),
    )

    nav_labels = []

    def switch_page(index):
        for page in pages:
            page.pack_forget()
        pages[index].pack(fill=tk.BOTH, expand=True)
        for nav_index, label in enumerate(nav_labels):
            label.configure(style="NavActive.TLabel" if nav_index == index else "Nav.TLabel")

    for index, title in enumerate(("MDL(Basic)", "MDL(Plus)", "NCM2MP3", "MVDL")):
        nav_labels.append(create_nav_item(nav_container, title, lambda index=index: switch_page(index), active=index == 0))

    switch_page(0)
    app.mainloop()


if __name__ == "__main__":
    run_app()
