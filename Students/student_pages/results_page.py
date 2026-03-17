import tkinter as tk

CARD_BG = "#ffffff"
TEXT_DARK = "#4a2c2c"
TEXT_MUTED = "#7a5c5c"
BORDER = "#eadede"


def show_results_page(app):
    box = tk.Frame(
        app.content_frame,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=BORDER
    )
    box.pack(fill="both", expand=True)

    tk.Label(
        box,
        text="Evaluation Results",
        font=("Segoe UI", 18, "bold"),
        fg=TEXT_DARK,
        bg=CARD_BG
    ).pack(anchor="w", padx=20, pady=(20, 15))

    completed = [item for item in app.evaluations_data if item["status"] == "submitted"]

    if not completed:
        tk.Label(
            box,
            text="No completed evaluations yet.",
            font=("Segoe UI", 11),
            fg=TEXT_MUTED,
            bg=CARD_BG
        ).pack(anchor="w", padx=20, pady=20)
        return

    for item in completed:
        card = tk.Frame(box, bg="#fcf7f7", highlightthickness=1, highlightbackground="#efe3e3")
        card.pack(fill="x", padx=20, pady=8)

        tk.Label(
            card,
            text=item["descriptive_title"],
            font=("Segoe UI", 11, "bold"),
            fg=TEXT_DARK,
            bg="#fcf7f7"
        ).pack(anchor="w", padx=15, pady=(12, 4))

        tk.Label(
            card,
            text=f"Faculty: {item['faculty_name']}",
            font=("Segoe UI", 10),
            fg=TEXT_MUTED,
            bg="#fcf7f7"
        ).pack(anchor="w", padx=15, pady=(0, 4))

        tk.Label(
            card,
            text="Status: Completed",
            font=("Segoe UI", 10, "bold"),
            fg="#3f6b4b",
            bg="#fcf7f7"
        ).pack(anchor="w", padx=15, pady=(0, 12))