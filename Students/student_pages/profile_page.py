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


def get_initials(full_name):
    if not full_name or full_name == "N/A":
        return "S"

    parts = full_name.split()
    if len(parts) == 1:
        return parts[0][0].upper()

    return (parts[0][0] + parts[-1][0]).upper()


def info_field(parent, label, value, row, column):
    field = tk.Frame(
        parent,
        bg=SOFT_BG,
        highlightthickness=1,
        highlightbackground=LIGHT_BORDER
    )
    field.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)

    tk.Label(
        field,
        text=label,
        font=("Segoe UI", 9, "bold"),
        fg=TEXT_SOFT,
        bg=SOFT_BG
    ).pack(anchor="w", padx=14, pady=(12, 4))

    tk.Label(
        field,
        text=value if value else "N/A",
        font=("Segoe UI", 11),
        fg=TEXT_DARK,
        bg=SOFT_BG,
        wraplength=320,
        justify="left"
    ).pack(anchor="w", padx=14, pady=(0, 12))


def show_profile_page(app):
    container = tk.Frame(app.content_frame, bg=PAGE_BG)
    container.pack(fill="both", expand=True)

    # Page Header
    tk.Label(
        container,
        text="My Profile",
        font=("Segoe UI", 20, "bold"),
        fg=TEXT_DARK,
        bg=PAGE_BG
    ).pack(anchor="w", padx=10, pady=(5, 4))

    tk.Label(
        container,
        text="View your personal and academic information.",
        font=("Segoe UI", 10),
        fg=TEXT_MUTED,
        bg=PAGE_BG
    ).pack(anchor="w", padx=10, pady=(0, 15))

    # Main Card
    main_card = tk.Frame(
        container,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=BORDER
    )
    main_card.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # Top Section
    top_section = tk.Frame(main_card, bg=CARD_BG)
    top_section.pack(fill="x", padx=24, pady=(24, 18))

    # Avatar section
    avatar_wrap = tk.Frame(top_section, bg=CARD_BG)
    avatar_wrap.pack(side="left", padx=(0, 20))

    full_name = app.student_info.get("full_name", "Student")
    initials = get_initials(full_name)

    avatar = tk.Canvas(
        avatar_wrap,
        width=90,
        height=90,
        bg=CARD_BG,
        highlightthickness=0,
        bd=0
    )
    avatar.pack()

    avatar.create_oval(5, 5, 85, 85, fill="#f3e4e4", outline="#e7cfcf")
    avatar.create_text(
        45, 45,
        text=initials,
        font=("Segoe UI", 24, "bold"),
        fill=ACCENT
    )

    # Name and status
    identity_wrap = tk.Frame(top_section, bg=CARD_BG)
    identity_wrap.pack(side="left", fill="both", expand=True)

    tk.Label(
        identity_wrap,
        text=full_name,
        font=("Segoe UI", 18, "bold"),
        fg=TEXT_DARK,
        bg=CARD_BG
    ).pack(anchor="w", pady=(10, 4))

    tk.Label(
        identity_wrap,
        text="Student Account",
        font=("Segoe UI", 10),
        fg=TEXT_MUTED,
        bg=CARD_BG
    ).pack(anchor="w")

    status_value = app.student_info.get("status", "N/A")
    status_bg = "#edf7ef" if status_value.lower() == "active" else "#fdf1f1"
    status_fg = "#3f6b4b" if status_value.lower() == "active" else "#8b4a4a"

    tk.Label(
        identity_wrap,
        text=status_value,
        font=("Segoe UI", 9, "bold"),
        fg=status_fg,
        bg=status_bg,
        padx=12,
        pady=5
    ).pack(anchor="w", pady=(10, 0))

    # Divider
    divider = tk.Frame(main_card, bg="#f1e7e7", height=1)
    divider.pack(fill="x", padx=24)

    # Information Section
    info_section = tk.Frame(main_card, bg=CARD_BG)
    info_section.pack(fill="both", expand=True, padx=16, pady=16)

    tk.Label(
        info_section,
        text="Profile Information",
        font=("Segoe UI", 12, "bold"),
        fg=TEXT_DARK,
        bg=CARD_BG
    ).grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(4, 10))

    info_section.grid_columnconfigure(0, weight=1)
    info_section.grid_columnconfigure(1, weight=1)

    info_field(
        info_section,
        "Full Name",
        app.student_info.get("full_name", "N/A"),
        row=1,
        column=0
    )

    info_field(
        info_section,
        "Student Number",
        app.student_info.get("student_no", "N/A"),
        row=1,
        column=1
    )

    info_field(
        info_section,
        "Program",
        app.student_info.get("program_name", "N/A"),
        row=2,
        column=0
    )

    info_field(
        info_section,
        "Email Address",
        app.student_info.get("email", "N/A"),
        row=2,
        column=1
    )

    info_field(
        info_section,
        "Account Status",
        app.student_info.get("status", "N/A"),
        row=3,
        column=0
    )

    info_field(
        info_section,
        "User Role",
        "Student",
        row=3,
        column=1
    )