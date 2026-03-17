import tkinter as tk

CARD_BG = "#ffffff"
PAGE_BG = "#fffafa"
TEXT_DARK = "#4a2c2c"
TEXT_MUTED = "#7a5c5c"
BORDER = "#eadede"

ACCENT = "#8b4a4a"
ACCENT_HOVER = "#723939"

SUCCESS = "#3f6b4b"
SUCCESS_HOVER = "#33563c"

STATUS_PENDING_BG = "#fdf1f1"
STATUS_PENDING_FG = "#8b4a4a"

STATUS_DONE_BG = "#edf7ef"
STATUS_DONE_FG = "#3f6b4b"


def show_evaluations_page(app):
    container = tk.Frame(app.content_frame, bg=PAGE_BG)
    container.pack(fill="both", expand=True)

    tk.Label(
        container,
        text="My Evaluations",
        font=("Segoe UI", 20, "bold"),
        fg=TEXT_DARK,
        bg=PAGE_BG
    ).pack(anchor="w", padx=10, pady=(5, 4))

    tk.Label(
        container,
        text="View your enrolled subjects and evaluate your instructors.",
        font=("Segoe UI", 10),
        fg=TEXT_MUTED,
        bg=PAGE_BG
    ).pack(anchor="w", padx=10, pady=(0, 15))

    if not app.subjects_data:
        empty_box = tk.Frame(
            container,
            bg=CARD_BG,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0
        )
        empty_box.pack(fill="x", padx=10, pady=10)

        tk.Label(
            empty_box,
            text="No enrolled subjects found.",
            font=("Segoe UI", 11),
            fg=TEXT_MUTED,
            bg=CARD_BG,
            pady=20
        ).pack()
        return

    evaluations_map = {
        item["class_offering_id"]: item
        for item in app.evaluations_data
    }

    cards_wrapper = tk.Frame(container, bg=PAGE_BG)
    cards_wrapper.pack(fill="both", expand=True)

    for item in app.subjects_data:
        evaluation = evaluations_map.get(item["class_offering_id"])

        if evaluation:
            if evaluation["status"] == "submitted":
                status_text = "Completed"
                status_bg = STATUS_DONE_BG
                status_fg = STATUS_DONE_FG
                btn_text = "Preview Evaluation"
                btn_bg = SUCCESS
                btn_hover = SUCCESS_HOVER
                btn_command = lambda data=item: app.preview_evaluation(data)
                helper_text = "You have already submitted your evaluation for this subject."
            else:
                status_text = "Pending"
                status_bg = STATUS_PENDING_BG
                status_fg = STATUS_PENDING_FG
                btn_text = "Evaluate"
                btn_bg = ACCENT
                btn_hover = ACCENT_HOVER
                btn_command = lambda data=item: app.open_evaluation(data)
                helper_text = "Your evaluation is not yet submitted. You may continue it."
        else:
            status_text = "Not Yet Started"
            status_bg = STATUS_PENDING_BG
            status_fg = STATUS_PENDING_FG
            btn_text = "Evaluate"
            btn_bg = ACCENT
            btn_hover = ACCENT_HOVER
            btn_command = lambda data=item: app.open_evaluation(data)
            helper_text = "You can now start evaluating this subject."

        card = tk.Frame(
            cards_wrapper,
            bg=CARD_BG,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0
        )
        card.pack(fill="x", padx=10, pady=7)

        top_section = tk.Frame(card, bg=CARD_BG)
        top_section.pack(fill="x", padx=18, pady=(16, 8))

        info_section = tk.Frame(top_section, bg=CARD_BG)
        info_section.pack(side="left", fill="both", expand=True)

        tk.Label(
            info_section,
            text=item["subject_code"],
            font=("Segoe UI", 10, "bold"),
            fg=ACCENT,
            bg=CARD_BG
        ).pack(anchor="w")

        tk.Label(
            info_section,
            text=item["descriptive_title"],
            font=("Segoe UI", 14, "bold"),
            fg=TEXT_DARK,
            bg=CARD_BG,
            wraplength=700,
            justify="left"
        ).pack(anchor="w", pady=(2, 6))

        tk.Label(
            info_section,
            text=f"Faculty: {item['faculty_name']}",
            font=("Segoe UI", 10),
            fg=TEXT_MUTED,
            bg=CARD_BG
        ).pack(anchor="w")

        right_section = tk.Frame(top_section, bg=CARD_BG)
        right_section.pack(side="right", anchor="n", padx=(10, 0))

        tk.Label(
            right_section,
            text=status_text,
            font=("Segoe UI", 9, "bold"),
            fg=status_fg,
            bg=status_bg,
            padx=12,
            pady=5
        ).pack(anchor="e")

        divider = tk.Frame(card, bg="#f1e7e7", height=1)
        divider.pack(fill="x", padx=18, pady=(4, 10))

        bottom_section = tk.Frame(card, bg=CARD_BG)
        bottom_section.pack(fill="x", padx=18, pady=(0, 15))

        tk.Label(
            bottom_section,
            text=helper_text,
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=CARD_BG
        ).pack(side="left")

        action_btn = tk.Button(
            bottom_section,
            text=btn_text,
            font=("Segoe UI", 10, "bold"),
            bg=btn_bg,
            fg="white",
            activebackground=btn_hover,
            activeforeground="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=8,
            command=btn_command
        )
        action_btn.pack(side="right")

        action_btn.bind("<Enter>", lambda e, c=btn_hover: e.widget.config(bg=c))
        action_btn.bind("<Leave>", lambda e, c=btn_bg: e.widget.config(bg=c))