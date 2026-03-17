import tkinter as tk

CARD_BG = "#ffffff"
TEXT_DARK = "#4a2c2c"
TEXT_MUTED = "#7a5c5c"
BORDER = "#eadede"


def show_subjects_page(app):
    box = tk.Frame(
        app.content_frame,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=BORDER
    )
    box.pack(fill="both", expand=True)

    tk.Label(
        box,
        text="My Subjects",
        font=("Segoe UI", 18, "bold"),
        fg=TEXT_DARK,
        bg=CARD_BG
    ).pack(anchor="w", padx=20, pady=(20, 15))

    header = tk.Frame(box, bg="#f4ebeb", height=40)
    header.pack(fill="x", padx=20)
    header.pack_propagate(False)

    tk.Label(header, text="Code", font=("Segoe UI", 10, "bold"), bg="#f4ebeb", fg=TEXT_DARK, width=15, anchor="w").pack(side="left", padx=(10, 0))
    tk.Label(header, text="Subject Title", font=("Segoe UI", 10, "bold"), bg="#f4ebeb", fg=TEXT_DARK, width=38, anchor="w").pack(side="left")
    tk.Label(header, text="Faculty", font=("Segoe UI", 10, "bold"), bg="#f4ebeb", fg=TEXT_DARK, width=25, anchor="w").pack(side="left")

    if not app.subjects_data:
        tk.Label(
            box,
            text="No enrolled subjects found.",
            font=("Segoe UI", 11),
            fg=TEXT_MUTED,
            bg=CARD_BG
        ).pack(anchor="w", padx=20, pady=20)
        return

    for i, item in enumerate(app.subjects_data, start=1):
        row_bg = "#ffffff" if i % 2 == 1 else "#fcf7f7"
        row = tk.Frame(box, bg=row_bg, height=42, highlightthickness=1, highlightbackground="#efe3e3")
        row.pack(fill="x", padx=20, pady=1)
        row.pack_propagate(False)

        tk.Label(row, text=item["subject_code"], font=("Segoe UI", 10), bg=row_bg, fg=TEXT_DARK, width=15, anchor="w").pack(side="left", padx=(10, 0))
        tk.Label(row, text=item["descriptive_title"], font=("Segoe UI", 10), bg=row_bg, fg=TEXT_DARK, width=38, anchor="w").pack(side="left")
        tk.Label(row, text=item["faculty_name"], font=("Segoe UI", 10), bg=row_bg, fg=TEXT_MUTED, width=25, anchor="w").pack(side="left")