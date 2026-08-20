import os
import threading

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog

from netease_music_tool.config import (
    APP_TITLE,
    BG_INPUT,
    BG_HOVER,
    BORDER,
    DESKTOP_PATH,
    FONT_FAMILY,
    PRIMARY_BLUE,
    STRIPE_BG,
    TEXT_HINT,
    TEXT_NORMAL,
    TEXT_WHITE,
    WINDOW_MIN_SIZE,
    WINDOW_SIZE,
)
from netease_music_tool.services.music_service import download_audio_by_info, fetch_song_info, parse_song_ids
from netease_music_tool.ui.theme import configure_application_theme


def create_nav_item(parent, text, command, active=False):
    style_name = 'NavActive.TLabel' if active else 'Nav.TLabel'
    label = ttk.Label(parent, text=text, style=style_name, cursor='hand2')
    label.pack(fill=tk.X)
    label.bind("<Button-1>", lambda e: command())
    return label


def set_status(status_label, text):
    status_label.config(text=text)


def run_app():
    app = ttk.Window(
        themename="darkly",
        title=APP_TITLE,
        size=WINDOW_SIZE,
        resizable=(True, True),
        minsize=WINDOW_MIN_SIZE,
    )
    download_save_path = tk.StringVar(value=DESKTOP_PATH)

    configure_application_theme()

    app.rowconfigure(0, weight=1)
    app.columnconfigure(0, weight=1)

    main_container = ttk.Frame(app)
    main_container.grid(row=0, column=0, sticky="nsew")

    sidebar = ttk.Frame(main_container, width=200)
    sidebar.pack(side=tk.LEFT, fill=tk.Y)
    sidebar.pack_propagate(False)

    ttk.Separator(sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=15, pady=(20, 10))

    nav_container = ttk.Frame(sidebar)
    nav_container.pack(fill=tk.X, pady=(10, 10))

    content_area = ttk.Frame(main_container)
    content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=tk.YES, padx=24, pady=24)

    page_1 = ttk.Frame(content_area)
    page_2 = ttk.Frame(content_area)

    def switch_page(index):
        page_1.pack_forget()
        page_2.pack_forget()
        if index == 0:
            page_1.pack(fill=tk.BOTH, expand=tk.YES)
            nav_labels[0].configure(style='NavActive.TLabel')
            nav_labels[1].configure(style='Nav.TLabel')
        else:
            page_2.pack(fill=tk.BOTH, expand=tk.YES)
            nav_labels[0].configure(style='Nav.TLabel')
            nav_labels[1].configure(style='NavActive.TLabel')

    nav_labels = []
    nav_labels.append(create_nav_item(nav_container, "Dawnloader v2", lambda: switch_page(0), active=True))
    nav_labels.append(create_nav_item(nav_container, "NCM to MP3", lambda: switch_page(1)))

    # page 1
    page_1.pack(fill=tk.BOTH, expand=tk.YES)

    ttk.Label(page_1, text="Dawnloader v2", font=(FONT_FAMILY, 16, 'bold')).pack(anchor=tk.W, pady=(0, 12))
    ttk.Label(page_1, text="利用旧版官方API下载, 只能下载免费歌曲", font=(FONT_FAMILY, 9), foreground=TEXT_HINT).pack(anchor=tk.W, pady=(0, 20))

    path_frame = ttk.Frame(page_1)
    path_frame.pack(fill=tk.X, pady=(0, 15))
    ttk.Label(path_frame, text="保存目录: ", font=(FONT_FAMILY, 10)).pack(side=tk.LEFT)
    path_entry = ttk.Entry(path_frame, textvariable=download_save_path, font=(FONT_FAMILY, 10))
    path_entry.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=(0, 10))

    def select_save_folder():
        folder = filedialog.askdirectory(title="选择下载保存文件夹")
        if folder:
            download_save_path.set(folder)

    folder_btn = ttk.Button(path_frame, text="选择目录", bootstyle="secondary", command=select_save_folder)
    folder_btn.pack(side=tk.LEFT)

    input_frame = ttk.Frame(page_1)
    input_frame.pack(fill=tk.X, pady=(0, 12))
    ttk.Label(input_frame, text="ID/链接列表", font=(FONT_FAMILY, 10)).pack(anchor=tk.W)
    ttk.Label(input_frame, text="粘贴歌曲ID或网页链接均可, 一行一条", font=(FONT_FAMILY, 9), foreground=TEXT_HINT).pack(anchor=tk.W, pady=(10, 5))

    song_id_text = tk.Text(
        input_frame,
        height=6,
        font=(FONT_FAMILY, 10),
        bg=BG_INPUT,
        fg=TEXT_NORMAL,
        insertbackground=TEXT_WHITE,
        relief='flat',
        borderwidth=1,
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=PRIMARY_BLUE,
    )
    song_id_text.pack(fill=tk.X, pady=(8, 12))

    text_placeholder = "https://music.163.com/#/song?id=1973665667\n1294924084"
    placeholder_visible = True
    song_id_text.insert("1.0", text_placeholder)
    song_id_text.tag_configure("placeholder", foreground=TEXT_HINT)
    song_id_text.tag_add("placeholder", "1.0", "end")

    def text_focus_in(event):
        nonlocal placeholder_visible
        if placeholder_visible:
            song_id_text.delete("1.0", tk.END)
            song_id_text.tag_remove("placeholder", "1.0", "end")
            song_id_text.config(fg=TEXT_NORMAL)
            placeholder_visible = False

    def text_focus_out(event):
        nonlocal placeholder_visible
        content = song_id_text.get("1.0", tk.END).strip()
        if content == "":
            song_id_text.insert("1.0", text_placeholder)
            song_id_text.tag_add("placeholder", "1.0", "end")
            song_id_text.config(fg=TEXT_HINT)
            placeholder_visible = True
        else:
            placeholder_visible = False

    song_id_text.bind("<FocusIn>", text_focus_in)
    song_id_text.bind("<FocusOut>", text_focus_out)

    btn_frame = ttk.Frame(page_1)
    btn_frame.pack(fill=tk.X, pady=(0, 12))

    list_frame = ttk.Frame(page_1)
    list_frame.pack(fill=tk.BOTH, expand=tk.YES, pady=(0, 12))

    columns = ("checked", "songid", "size", "status")
    tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
    tree.heading("checked", text="选择")
    tree.heading("songid", text="歌曲ID")
    tree.heading("size", text="文件大小")
    tree.heading("status", text="状态")
    tree.column("checked", width=60, anchor=tk.CENTER, stretch=False)
    tree.column("songid", width=220, anchor=tk.CENTER)
    tree.column("size", width=140, anchor=tk.CENTER)
    tree.column("status", width=220, anchor=tk.CENTER)

    scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    checkbox_vars = {}
    checkbox_widgets = {}

    def position_checkboxes():
        for item, checkbox in checkbox_widgets.items():
            bbox = tree.bbox(item, "#1")
            if not bbox:
                checkbox.place_forget()
                continue
            x, y, width, height = bbox
            checkbox.place(
                x=tree.winfo_x() + x + (width - 28) // 2,
                y=tree.winfo_y() + y + (height - 28) // 2,
                width=28,
                height=28,
            )

    def on_tree_scroll(*args):
        scrollbar.set(*args)
        position_checkboxes()

    tree.configure(yscrollcommand=on_tree_scroll)
    tree.bind("<Configure>", lambda event: position_checkboxes())

    tree.tag_configure('odd', background=BG_INPUT)
    tree.tag_configure('even', background=STRIPE_BG)
    tree.tag_configure('checked', foreground=PRIMARY_BLUE)
    tree.tag_configure('unchecked', foreground=TEXT_HINT)

    def refresh_row_tags(item):
        values = tree.item(item, "values")
        if not values:
            return
        idx = tree.index(item)
        tag1 = 'even' if idx % 2 == 0 else 'odd'
        checkbox_var = checkbox_vars.get(item)
        tag2 = 'checked' if checkbox_var and checkbox_var.get() else 'unchecked'
        tree.item(item, tags=(tag1, tag2))

    def add_checkbox(item):
        checkbox_var = tk.BooleanVar(value=False)
        checkbox = tk.Checkbutton(
            list_frame,
            variable=checkbox_var,
            command=lambda: refresh_row_tags(item),
            indicatoron=True,
            width=1,
            height=1,
            bd=0,
            highlightthickness=0,
            bg=BG_INPUT,
            activebackground=BG_HOVER,
            selectcolor=BG_INPUT,
            activeforeground=TEXT_WHITE,
            fg=TEXT_NORMAL,
            relief=tk.FLAT,
        )
        checkbox_vars[item] = checkbox_var
        checkbox_widgets[item] = checkbox
        app.after_idle(position_checkboxes)

    status_label = ttk.Label(app, text="就绪", style="Status.TLabel")
    status_label.grid(row=1, column=0, sticky="ew")

    song_info_list = []

    def show_fetch_results(result_list):
        nonlocal song_info_list
        song_info_list.clear()
        for checkbox in checkbox_widgets.values():
            checkbox.destroy()
        checkbox_vars.clear()
        checkbox_widgets.clear()
        for item in tree.get_children():
            tree.delete(item)

        for item in result_list:
            if not item.get("ok"):
                song_info_list.append({
                    "id": item["id"],
                    "ok": False,
                    "url": None,
                    "size": 0,
                })
                inserted = tree.insert("", tk.END, values=("", item["id"], "-", "获取失败(无音频链接)"))
                add_checkbox(inserted)
                refresh_row_tags(inserted)
                continue

            song_info_list.append({
                "id": str(item["id"]),
                "ok": True,
                "url": item["url"],
                "size": item["size"],
            })
            inserted = tree.insert("", tk.END, values=("", item["id"], item.get("size_text", "-"), "可下载"))
            add_checkbox(inserted)
            refresh_row_tags(inserted)

        set_status(status_label, "歌曲信息获取完成")
        fetch_btn.configure(state=tk.NORMAL)

    def fetch_info():
        raw_text = song_id_text.get("1.0", tk.END).strip()
        if raw_text == "":
            set_status(status_label, "请输入歌曲 ID 或链接")
            return

        id_list = parse_song_ids(raw_text)
        if not id_list:
            set_status(status_label, "未找到有效的歌曲 ID")
            return

        set_status(status_label, f"开始获取 {len(id_list)} 首歌曲信息...")
        fetch_btn.configure(state=tk.DISABLED)

        def request_song_info():
            try:
                result_list = fetch_song_info(id_list)
            except Exception as exc:
                app.after(0, lambda error=exc: finish_fetch_error(error))
                return
            app.after(0, lambda: show_fetch_results(result_list))

        threading.Thread(target=request_song_info, daemon=True).start()

    def finish_fetch_error(error):
        fetch_btn.configure(state=tk.NORMAL)
        set_status(status_label, f"获取失败: {error}")

    def download_selected():
        save_dir = download_save_path.get()
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        items = tree.get_children()
        success = 0
        fail = 0

        for item_id in items:
            row = tree.item(item_id)["values"]
            _, sid, _, _ = row
            checkbox_var = checkbox_vars.get(item_id)
            if not checkbox_var or not checkbox_var.get():
                continue

            info = next((x for x in song_info_list if x["id"] == str(sid)), None)
            if not info or not info["ok"] or not info["url"]:
                fail += 1
                continue

            if download_audio_by_info(info, save_dir, lambda text: set_status(status_label, text)):
                success += 1
                tree.set(item_id, "status", "下载完成")
            else:
                fail += 1
                tree.set(item_id, "status", "下载失败")

        set_status(status_label, f"下载任务结束，成功{success}首，失败{fail}首")

    def set_all_checkboxes(selected):
        for item_id, checkbox_var in checkbox_vars.items():
            checkbox_var.set(selected)
            refresh_row_tags(item_id)

    def delete_rows(item_ids):
        deleted_ids = set()
        for item_id in item_ids:
            row = tree.item(item_id)["values"]
            if row:
                deleted_ids.add(str(row[1]))
            checkbox = checkbox_widgets.pop(item_id, None)
            if checkbox:
                checkbox.destroy()
            checkbox_vars.pop(item_id, None)
            tree.delete(item_id)

        song_info_list[:] = [info for info in song_info_list if info["id"] not in deleted_ids]
        position_checkboxes()

    def delete_selected():
        selected_items = [
            item_id for item_id, checkbox_var in checkbox_vars.items() if checkbox_var.get()
        ]
        if not selected_items:
            set_status(status_label, "请先选择要删除的歌曲")
            return
        delete_rows(selected_items)
        set_status(status_label, f"已删除 {len(selected_items)} 首歌曲")

    def delete_all():
        all_items = list(tree.get_children())
        if not all_items:
            set_status(status_label, "列表已经为空")
            return
        delete_rows(all_items)
        set_status(status_label, "已删除全部歌曲")

    fetch_btn = ttk.Button(btn_frame, text="获取信息", bootstyle="primary", command=fetch_info)
    fetch_btn.pack(side=tk.LEFT, padx=(0, 10))

    dl_btn = ttk.Button(btn_frame, text="下载选中项", bootstyle="primary", command=download_selected)
    dl_btn.pack(side=tk.LEFT, padx=(0, 10))

    ttk.Button(btn_frame, text="全选", bootstyle="secondary", command=lambda: set_all_checkboxes(True)).pack(side=tk.LEFT, padx=(0, 6))
    ttk.Button(btn_frame, text="取消全选", bootstyle="secondary", command=lambda: set_all_checkboxes(False)).pack(side=tk.LEFT, padx=(0, 6))
    ttk.Button(btn_frame, text="删除选中", bootstyle="secondary", command=delete_selected).pack(side=tk.LEFT, padx=(0, 6))
    ttk.Button(btn_frame, text="全部删除", bootstyle="secondary", command=delete_all).pack(side=tk.LEFT)
 
    # page 2
    ttk.Label(page_2, text="NCM解析", font=(FONT_FAMILY, 16, 'bold')).pack(anchor=tk.W, pady=(0, 12))
    ttk.Label(page_2, text="上传 .ncm 文件进行解析，转换为标准音频格式", font=(FONT_FAMILY, 9), foreground=TEXT_HINT).pack(anchor=tk.W, pady=(0, 30))

    upload_frame = ttk.Frame(page_2, padding=30)
    upload_frame.pack(fill=tk.X, pady=(0, 18))

    upload_label = ttk.Label(
        upload_frame,
        text="点击选择文件或拖拽文件到此区域",
        font=(FONT_FAMILY, 11),
        anchor=tk.CENTER,
        justify=tk.CENTER,
    )
    upload_label.pack(fill=tk.X, pady=20)

    file_status = ttk.Label(upload_frame, text="未选择文件", font=(FONT_FAMILY, 9), foreground=TEXT_HINT)
    file_status.pack()

    def select_file():
        file_path = filedialog.askopenfilename(title="选择 NCM 文件", filetypes=[("NCM 文件", "*.ncm"), ("所有文件", "*.*")])
        if file_path:
            filename = os.path.basename(file_path)
            file_status.configure(text=f"已选择: {filename}")
            set_status(status_label, f"已选择文件: {filename}")

    upload_btn = ttk.Button(upload_frame, text="选择文件", bootstyle="secondary", command=select_file)
    upload_btn.pack(pady=(0, 10))

    def parse_file():
        if file_status.cget('text') != "未选择文件":
            set_status(status_label, "开始解析文件...")
            app.after(1000, lambda: set_status(status_label, "解析完成"))
        else:
            set_status(status_label, "请先选择文件")

    parse_btn = ttk.Button(page_2, text="开始解析", bootstyle="primary", padding=(20, 10), command=parse_file)
    parse_btn.pack(pady=(12, 0))

    ttk.Label(page_2, text="提示：上传 .ncm 文件后点击开始解析进行转换", font=(FONT_FAMILY, 8), foreground=TEXT_HINT).pack(anchor=tk.W, pady=(18, 0))

    page_1.pack(fill=tk.BOTH, expand=tk.YES)
    app.mainloop()


if __name__ == "__main__":
    run_app()
