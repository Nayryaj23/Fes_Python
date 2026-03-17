import tkinter as tk

CARD_BG = "#ffffff"
CONTENT_BG = "#fffafa"
TEXT_DARK = "#4a2c2c"
TEXT_MUTED = "#7a5c5c"
ACCENT = "#8b4a4a"
BORDER = "#eadede"


def create_stat_card(parent, title, value):
    card = tk.Frame(
        parent,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=BORDER
    )
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
        text="Student Dashboard Overview",
        font=("Segoe UI", 18, "bold"),
        fg=TEXT_DARK,
        bg=CONTENT_BG
    ).pack(anchor="w", pady=(0, 15))

    cards_frame = tk.Frame(app.content_frame, bg=CONTENT_BG)
    cards_frame.pack(fill="x")

    total_subjects = len(app.subjects_data)
    pending_count = sum(1 for item in app.evaluations_data if item["status"] == "draft")
    completed_count = sum(1 for item in app.evaluations_data if item["status"] == "submitted")

    create_stat_card(cards_frame, "Enrolled Subjects", str(total_subjects))
    create_stat_card(cards_frame, "Pending Evaluations", str(pending_count))
    create_stat_card(cards_frame, "Completed Evaluations", str(completed_count))

    lower_frame = tk.Frame(app.content_frame, bg=CONTENT_BG)
    lower_frame.pack(fill="both", expand=True, pady=20)

    left_panel = tk.Frame(lower_frame, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER)
    left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

    tk.Label(
        left_panel,
        text="Student Information",
        font=("Segoe UI", 14, "bold"),
        fg=TEXT_DARK,
        bg=CARD_BG
    ).pack(anchor="w", padx=20, pady=15)

    info_lines = [
        f"Name: {app.student_info.get('full_name', 'N/A')}",
        f"Student No: {app.student_info.get('student_no', 'N/A')}",
        f"Program: {app.student_info.get('program_name', 'N/A')}",
        f"Status: {app.student_info.get('status', 'N/A')}",
    ]

    for line in info_lines:
        tk.Label(
            left_panel,
            text=line,
            font=("Segoe UI", 11),
            fg=TEXT_MUTED,
            bg=CARD_BG
        ).pack(anchor="w", padx=20, pady=6)

    right_panel = tk.Frame(lower_frame, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER)
    right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))

    tk.Label(
        right_panel,
        text="Recent Evaluation Status",
        font=("Segoe UI", 14, "bold"),
        fg=TEXT_DARK,
        bg=CARD_BG
    ).pack(anchor="w", padx=20, pady=15)

    if not app.evaluations_data:
        tk.Label(
            right_panel,
            text="No evaluations found.",
            font=("Segoe UI", 11),
            fg=TEXT_MUTED,
            bg=CARD_BG
        ).pack(anchor="w", padx=20, pady=6)
    else:
        for item in app.evaluations_data[:5]:
            status_text = "Pending" if item["status"] == "draft" else "Completed"
            tk.Label(
                right_panel,
                text=f"• {item['descriptive_title']} - {status_text}",
                font=("Segoe UI", 11),
                fg=TEXT_MUTED,
                bg=CARD_BG,
                justify="left",
                wraplength=420
            ).pack(anchor="w", padx=20, pady=6)