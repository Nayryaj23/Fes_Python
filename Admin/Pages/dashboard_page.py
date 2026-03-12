import tkinter as tk

CARD_BG = "#ffffff"
CONTENT_BG = "#fffafa"
TEXT_DARK = "#4a2c2c"
TEXT_MUTED = "#7a5c5c"
ACCENT = "#8b4a4a"
BORDER = "#eadede"


def create_stat_card(parent, title, value):
    card = tk.Frame(parent, bg=CARD_BG, bd=0, highlightthickness=1, highlightbackground=BORDER)
    card.pack(side="left", padx=10, pady=10, fill="both", expand=True)

    tk.Label(
        card,
        text=title,
        font=("Segoe UI", 11),
        fg=TEXT_MUTED,
        bg=CARD_BG
    ).pack(anchor="w", padx=20, pady=(20, 5))

    tk.Label(
        card,
        text=value,
        font=("Segoe UI", 24, "bold"),
        fg=ACCENT,
        bg=CARD_BG
    ).pack(anchor="w", padx=20, pady=(0, 20))


def show_dashboard_page(app):
    tk.Label(
        app.content_frame,
        text="Dashboard Overview",
        font=("Segoe UI", 18, "bold"),
        fg=TEXT_DARK,
        bg=CONTENT_BG
    ).pack(anchor="w", pady=(0, 15))

    cards_frame = tk.Frame(app.content_frame, bg=CONTENT_BG)
    cards_frame.pack(fill="x")

    create_stat_card(cards_frame, "Total Faculty", "25")
    create_stat_card(cards_frame, "Total Students", "1,240")
    create_stat_card(cards_frame, "Active Evaluations", "3")
    create_stat_card(cards_frame, "Reports Generated", "18")