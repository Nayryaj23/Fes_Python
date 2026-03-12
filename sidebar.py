import tkinter as tk
import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class Sidebar(tk.Frame):
    def __init__(
        self,
        parent,
        title="Dashboard Menu",
        menu_items=None,
        on_menu_click=None,
        bg="#6d3b3b",
        logo_path="resources/LogoSPC.png"
    ):
        super().__init__(parent, bg=bg, width=240)
        self.pack_propagate(False)

        self.bg = bg
        self.hover_bg = "#8b4a4a"
        self.active_bg = "#9b5c5c"
        self.normal_bg = bg
        self.text_color = "#ffffff"
        self.group_text_color = "#e7c7c7"
        self.on_menu_click = on_menu_click
        self.active_item = None
        self.buttons = {}

        if menu_items is None:
            menu_items = {}

        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_logo_path = os.path.join(base_dir, logo_path)

        # ---------------- HEADER ----------------
        header_frame = tk.Frame(self, bg=self.bg, height=140)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        if PIL_AVAILABLE:
            try:
                logo = Image.open(full_logo_path).convert("RGBA")
                logo = logo.resize((70, 70), Image.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(logo)

                logo_label = tk.Label(
                    header_frame,
                    image=self.logo_img,
                    bg=self.bg
                )
                logo_label.pack(pady=(15, 5))
            except Exception:
                self.create_text_logo(header_frame)
        else:
            self.create_text_logo(header_frame)

        title_label = tk.Label(
            header_frame,
            text=title,
            font=("Segoe UI", 11, "bold"),
            fg="white",
            bg=self.bg
        )
        title_label.pack()

        divider = tk.Frame(self, bg="#9f6a6a", height=1)
        divider.pack(fill="x", padx=15, pady=(10, 15))

        # ---------------- GROUPED MENU ----------------
        menu_area = tk.Frame(self, bg=self.bg)
        menu_area.pack(fill="x")

        for group_name, items in menu_items.items():
            group_label = tk.Label(
                menu_area,
                text=group_name.upper(),
                font=("Segoe UI", 9, "bold"),
                fg=self.group_text_color,
                bg=self.bg,
                anchor="w"
            )
            group_label.pack(fill="x", padx=18, pady=(10, 4))

            for item in items:
                btn = tk.Label(
                    menu_area,
                    text="  " + item,
                    font=("Segoe UI", 11),
                    fg=self.text_color,
                    bg=self.normal_bg,
                    anchor="w",
                    padx=20,
                    pady=11,
                    cursor="hand2"
                )
                btn.pack(fill="x", padx=10, pady=2)

                btn.bind("<Enter>", lambda e, b=btn, name=item: self.on_hover_in(b, name))
                btn.bind("<Leave>", lambda e, b=btn, name=item: self.on_hover_out(b, name))
                btn.bind("<Button-1>", lambda e, name=item: self.menu_clicked(name))

                self.buttons[item] = btn

        # ---------------- SPACER ----------------
        self.spacer = tk.Frame(self, bg=self.bg)
        self.spacer.pack(fill="both", expand=True)

        # ---------------- LOGOUT BUTTON ----------------
        logout_container = tk.Frame(self, bg=self.bg)
        logout_container.pack(fill="x", padx=12, pady=(5, 12))

        self.logout_btn = tk.Label(
            logout_container,
            text="Logout",
            font=("Segoe UI", 11, "bold"),
            fg="white",
            bg="#b23b3b",
            anchor="center",
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.logout_btn.pack(fill="x")

        self.logout_btn.bind("<Enter>", lambda e: self.logout_btn.config(bg="#d14a4a"))
        self.logout_btn.bind("<Leave>", lambda e: self.logout_btn.config(bg="#b23b3b"))
        self.logout_btn.bind("<Button-1>", lambda e: self.menu_clicked("Logout"))

    def create_text_logo(self, parent):
        logo_label = tk.Label(
            parent,
            text="FES",
            font=("Segoe UI", 24, "bold"),
            fg="white",
            bg=self.bg
        )
        logo_label.pack(pady=(15, 5))

    def menu_clicked(self, item_name):
        if item_name != "Logout":
            self.set_active(item_name)

        if self.on_menu_click:
            self.on_menu_click(item_name)

    def set_active(self, active_item):
        self.active_item = active_item

        for name, btn in self.buttons.items():
            if name == active_item:
                btn.config(bg=self.active_bg, font=("Segoe UI", 11, "bold"))
            else:
                btn.config(bg=self.normal_bg, font=("Segoe UI", 11))

    def on_hover_in(self, button, name):
        if name != self.active_item:
            button.config(bg=self.hover_bg)

    def on_hover_out(self, button, name):
        if name != self.active_item:
            button.config(bg=self.normal_bg)