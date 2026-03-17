import tkinter as tk

PAGE_BG = "#fffafa"
CARD_BG = "#ffffff"
SOFT_BG = "#fcf7f7"
TEXT_DARK = "#4a2c2c"
TEXT_MUTED = "#7a5c5c"
TEXT_SOFT = "#a17f7f"
ACCENT = "#8b4a4a"
BORDER = "#eadede"
LIGHT_BORDER = "#f1e4e4"

SUCCESS_BG = "#edf7ef"
SUCCESS_FG = "#3f6b4b"

PENDING_BG = "#fdf1f1"
PENDING_FG = "#8b4a4a"


def create_stat_card(parent, title, value, subtitle, accent_color=ACCENT):
    card = tk.Frame(
        parent,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=BORDER
    )
    card.pack(side="left", padx=8, pady=0, fill="both", expand=True)

    tk.Label(
        card,
        text=title,
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_SOFT,
        bg=CARD_BG
    ).pack(anchor="w", padx=18, pady=(18, 6))

    tk.Label(
        card,
        text=value,
        font=("Segoe UI", 24, "bold"),
        fg=accent_color,
        bg=CARD_BG
    ).pack(anchor="w", padx=18)

    tk.Label(
        card,
        text=subtitle,
        font=("Segoe UI", 9),
        fg=TEXT_MUTED,
        bg=CARD_BG
    ).pack(anchor="w", padx=18, pady=(6, 18))


def create_info_row(parent, label, value):
    row = tk.Frame(parent, bg=SOFT_BG, highlightthickness=1, highlightbackground=LIGHT_BORDER)
    row.pack(fill="x", padx=18, pady=6)

    tk.Label(
        row,
        text=label,
        font=("Segoe UI", 9, "bold"),
        fg=TEXT_SOFT,
        bg=SOFT_BG,
        width=14,
        anchor="w"
    ).pack(side="left", padx=(14, 8), pady=12)

    tk.Label(
        row,
        text=value if value else "N/A",
        font=("Segoe UI", 10),
        fg=TEXT_DARK,
        bg=SOFT_BG,
        anchor="w"
    ).pack(side="left", fill="x", expand=True, pady=12)


def create_status_chip(parent, status_text):
    if status_text.lower() == "completed":
        bg = SUCCESS_BG
        fg = SUCCESS_FG
    else:
        bg = PENDING_BG
        fg = PENDING_FG

    chip = tk.Label(
        parent,
        text=status_text,
        font=("Segoe UI", 9, "bold"),
        fg=fg,
        bg=bg,
        padx=10,
        pady=4
    )
    return chip


def show_dashboard_page(app):
    container = tk.Frame(app.content_frame, bg=PAGE_BG)
    container.pack(fill="both", expand=True)

    total_subjects = len(app.subjects_data)
    pending_count = sum(1 for item in app.evaluations_data if item["status"] == "draft")
    completed_count = sum(1 for item in app.evaluations_data if item["status"] == "submitted")

    # Header
    tk.Label(
        container,
        text="Student Dashboard Overview",
        font=("Segoe UI", 20, "bold"),
        fg=TEXT_DARK,
        bg=PAGE_BG
    ).pack(anchor="w", padx=10, pady=(5, 4))
    #
    tk.Label(
        container,
        text="Monitor your academic information and evaluation progress.",
        font=("Segoe UI", 10),
        fg=TEXT_MUTED,
        bg=PAGE_BG
    ).pack(anchor="w", padx=10, pady=(0, 15))
    #
    # # Welcome Card
    # welcome_card = tk.Frame(
    #     container,
    #     bg=CARD_BG,
    #     highlightthickness=1,
    #     highlightbackground=BORDER
    # )
    # welcome_card.pack(fill="x", padx=10, pady=(0, 12))
    #
    # tk.Label(
    #     welcome_card,
    #     text=f"Welcome, {app.student_info.get('full_name', 'Student')}",
    #     font=("Segoe UI", 16, "bold"),
    #     fg=TEXT_DARK,
    #     bg=CARD_BG
    # ).pack(anchor="w", padx=20, pady=(18, 6))
    #
    # tk.Label(
    #     welcome_card,
    #     text="Here is a quick summary of your enrolled subjects and evaluation activity.",
    #     font=("Segoe UI", 10),
    #     fg=TEXT_MUTED,
    #     bg=CARD_BG
    # ).pack(anchor="w", padx=20, pady=(0, 18))
    #
    # Stats
    stats_frame = tk.Frame(container, bg=PAGE_BG)
    stats_frame.pack(fill="x", padx=10, pady=(0, 14))

    create_stat_card(
        stats_frame,
        "Enrolled Subjects",
        str(total_subjects),
        "Subjects currently enrolled"
    )

    create_stat_card(
        stats_frame,
        "Pending Evaluations",
        str(pending_count),
        "Evaluations not yet submitted"
    )

    create_stat_card(
        stats_frame,
        "Completed Evaluations",
        str(completed_count),
        "Successfully submitted"
    )

    # Lower panels
    lower_frame = tk.Frame(container, bg=PAGE_BG)
    lower_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # # Left Panel - Student Info
    # left_panel = tk.Frame(
    #     lower_frame,
    #     bg=CARD_BG,
    #     highlightthickness=1,
    #     highlightbackground=BORDER
    # )
    # left_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))

    # tk.Label(
    #     left_panel,
    #     text="Student Information",
    #     font=("Segoe UI", 13, "bold"),
    #     fg=TEXT_DARK,
    #     bg=CARD_BG
    # ).pack(anchor="w", padx=18, pady=(18, 12))

    # create_info_row(left_panel, "Full Name", app.student_info.get("full_name", "N/A"))
    # create_info_row(left_panel, "Student No.", app.student_info.get("student_no", "N/A"))
    # create_info_row(left_panel, "Program", app.student_info.get("program_name", "N/A"))
    # create_info_row(left_panel, "Status", app.student_info.get("status", "N/A"))

    # Right Panel - Recent Evaluations
    right_panel = tk.Frame(
        lower_frame,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=BORDER
    )
    right_panel.pack(side="right", fill="both", expand=True, padx=(8, 0))

    tk.Label(
        right_panel,
        text="Recent Evaluation Status",
        font=("Segoe UI", 13, "bold"),
        fg=TEXT_DARK,
        bg=CARD_BG
    ).pack(anchor="w", padx=18, pady=(18, 12))

    if not app.evaluations_data:
        empty_box = tk.Frame(
            right_panel,
            bg=SOFT_BG,
            highlightthickness=1,
            highlightbackground=LIGHT_BORDER
        )
        empty_box.pack(fill="x", padx=18, pady=6)

        tk.Label(
            empty_box,
            text="No evaluations found.",
            font=("Segoe UI", 10),
            fg=TEXT_MUTED,
            bg=SOFT_BG,
            pady=16
        ).pack()
    else:
        for item in app.evaluations_data[:5]:
            row = tk.Frame(
                right_panel,
                bg=SOFT_BG,
                highlightthickness=1,
                highlightbackground=LIGHT_BORDER
            )
            row.pack(fill="x", padx=18, pady=6)

            left = tk.Frame(row, bg=SOFT_BG)
            left.pack(side="left", fill="both", expand=True, padx=14, pady=12)

            tk.Label(
                left,
                text=item["descriptive_title"],
                font=("Segoe UI", 10, "bold"),
                fg=TEXT_DARK,
                bg=SOFT_BG,
                anchor="w",
                justify="left",
                wraplength=280
            ).pack(anchor="w")

            tk.Label(
                left,
                text=item.get("subject_code", ""),
                font=("Segoe UI", 9),
                fg=TEXT_SOFT,
                bg=SOFT_BG
            ).pack(anchor="w", pady=(3, 0))

            status_text = "Pending" if item["status"] == "draft" else "Completed"

            right = tk.Frame(row, bg=SOFT_BG)
            right.pack(side="right", padx=14, pady=12)

            chip = create_status_chip(right, status_text)
            chip.pack()

    # Bottom note
    note_card = tk.Frame(
        container,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=BORDER
    )
    note_card.pack(fill="x", padx=10, pady=(0, 0))

    tk.Label(
        note_card,
        text="Tip: Complete your pending evaluations on time to keep your records updated.",
        font=("Segoe UI", 9),
        fg=TEXT_MUTED,
        bg=CARD_BG
    ).pack(anchor="w", padx=18, pady=14)