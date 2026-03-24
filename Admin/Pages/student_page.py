import tkinter as tk

CARD_BG = "#ffffff"
CONTENT_BG = "#fffafa"
TEXT_DARK = "#4a2c2c"
TEXT_MUTED = "#7a5c5c"
ACCENT = "#8b4a4a"
BORDER = "#eadede"


def show_students_page(app):
    tk.Label(
        app.content_frame,
        text="Student Page",
        font=("Segoe UI", 18, "bold"),
        fg=TEXT_DARK,
        bg=CONTENT_BG
    ).pack(anchor="w", pady=(0, 15))


