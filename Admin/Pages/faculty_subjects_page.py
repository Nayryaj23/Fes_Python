import tkinter as tk
from tkinter import ttk, messagebox
from db_connection import get_connection

BG_MAIN = "#f7f3f3"
CARD_BG = "#ffffff"
TEXT_DARK = "#4a2c2c"
TEXT_MUTED = "#7a5c5c"
ACCENT = "#8b4a4a"
ACCENT_HOVER = "#723939"
BORDER = "#ddd0d0"
ROW_ALT = "#fcf7f7"
ROW_WHITE = "#ffffff"
ACTION_TEXT = "[ View Result ]"


def fetch_subjects_of_faculty_in_period(evaluation_period_id, faculty_id, search_text=""):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                co.id AS class_offering_id,
                s.subject_code,
                s.descriptive_title,
                sec.year_level,
                sec.section_name,
                sem.name AS semester,
                sy.year_label AS school_year,
                COALESCE(co.schedule, '') AS schedule
            FROM evaluations e
            INNER JOIN class_offerings co ON co.id = e.class_offering_id
            INNER JOIN subjects s ON s.id = co.subject_id
            INNER JOIN sections sec ON sec.id = co.section_id
            INNER JOIN terms t ON t.id = co.term_id
            INNER JOIN semesters sem ON sem.id = t.semester_id
            INNER JOIN school_years sy ON sy.id = t.school_year_id
            WHERE e.evaluation_period_id = %s
              AND co.faculty_id = %s
        """

        params = [evaluation_period_id, faculty_id]

        if search_text.strip():
            query += """
                AND (
                    s.subject_code LIKE %s
                    OR s.descriptive_title LIKE %s
                    OR sec.section_name LIKE %s
                    OR sem.name LIKE %s
                    OR sy.year_label LIKE %s
                    OR co.schedule LIKE %s
                )
            """
            like_value = f"%{search_text.strip()}%"
            params.extend([like_value] * 6)

        query += """
            GROUP BY
                co.id,
                s.subject_code,
                s.descriptive_title,
                sec.year_level,
                sec.section_name,
                sem.name,
                sy.year_label,
                co.schedule
            ORDER BY
                s.subject_code ASC,
                sec.year_level ASC,
                sec.section_name ASC
        """

        cursor.execute(query, params)
        return cursor.fetchall()

    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load subject list.\n\n{e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def show_faculty_subjects_page(app):
    parent = app.content_frame

    for widget in parent.winfo_children():
        widget.destroy()

    if not getattr(app, "selected_faculty_id", None):
        empty_frame = tk.Frame(parent, bg=BG_MAIN)
        empty_frame.pack(fill="both", expand=True)

        tk.Label(
            empty_frame,
            text="No Faculty Selected",
            font=("Segoe UI", 22, "bold"),
            bg=BG_MAIN,
            fg=TEXT_DARK
        ).pack(pady=(90, 10))

        tk.Label(
            empty_frame,
            text="Please select a faculty first before viewing handled subjects.",
            font=("Segoe UI", 11),
            bg=BG_MAIN,
            fg=TEXT_MUTED
        ).pack()
        return

    def open_result_from_values(values):
        if not values:
            return

        subject_code = values[0]
        subject_title = values[1]

        matched_subject = None
        for row in subject_cache:
            if row["subject_code"] == subject_code and row["descriptive_title"] == subject_title:
                matched_subject = row
                break

        if not matched_subject:
            messagebox.showwarning("Selection Error", "Unable to determine selected subject.")
            return

        app.selected_class_offering_id = matched_subject["class_offering_id"]
        app.selected_subject_name = f"{matched_subject['subject_code']} - {matched_subject['descriptive_title']}"
        app.show_evaluation_result_page()

    # ================= HEADER =================
    header_frame = tk.Frame(parent, bg=BG_MAIN)
    header_frame.pack(fill="x", pady=(0, 14))

    top_header_row = tk.Frame(header_frame, bg=BG_MAIN)
    top_header_row.pack(fill="x")

    def go_back():
        app.show_faculty_page()

    tk.Button(
        top_header_row,
        text="← Back",
        font=("Segoe UI", 10, "bold"),
        bg="#6c757d",
        fg="white",
        activebackground="#5b636a",
        activeforeground="white",
        relief="flat",
        bd=0,
        padx=14,
        pady=7,
        cursor="hand2",
        command=go_back
    ).pack(side="left")

    title_frame = tk.Frame(header_frame, bg=BG_MAIN)
    title_frame.pack(fill="x", pady=(12, 0))

    tk.Label(
        title_frame,
        text="Subject List",
        font=("Segoe UI", 20, "bold"),
        bg=BG_MAIN,
        fg=TEXT_DARK
    ).pack(anchor="w")

    tk.Label(
        title_frame,
        text=f"Handled subjects of {app.selected_faculty_name} in the active evaluation period",
        font=("Segoe UI", 10),
        bg=BG_MAIN,
        fg=TEXT_MUTED
    ).pack(anchor="w", pady=(4, 0))

    # ================= SEARCH CARD =================
    search_card = tk.Frame(
        parent,
        bg=CARD_BG,
        bd=1,
        relief="solid",
        highlightbackground=BORDER,
        highlightthickness=1
    )
    search_card.pack(fill="x", pady=(0, 14))

    search_inner = tk.Frame(search_card, bg=CARD_BG)
    search_inner.pack(fill="x", padx=16, pady=14)

    tk.Label(
        search_inner,
        text="Search Subject",
        font=("Segoe UI", 10, "bold"),
        bg=CARD_BG,
        fg=TEXT_DARK
    ).pack(side="left", padx=(0, 10))

    search_var = tk.StringVar()
    search_entry = tk.Entry(
        search_inner,
        textvariable=search_var,
        font=("Segoe UI", 10),
        relief="solid",
        bd=1,
        width=36
    )
    search_entry.pack(side="left", padx=(0, 10), ipady=3)

    # ================= TABLE CARD =================
    table_card = tk.Frame(
        parent,
        bg=CARD_BG,
        bd=1,
        relief="solid",
        highlightbackground=BORDER,
        highlightthickness=1
    )
    table_card.pack(fill="both", expand=True)

    top_info_frame = tk.Frame(table_card, bg=CARD_BG)
    top_info_frame.pack(fill="x", padx=16, pady=(14, 8))

    tk.Label(
        top_info_frame,
        text="Click the action button in the same row to view the evaluation result.",
        font=("Segoe UI", 10),
        bg=CARD_BG,
        fg=TEXT_MUTED
    ).pack(anchor="w")

    table_frame = tk.Frame(table_card, bg=CARD_BG)
    table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    columns = ("subject_code", "title", "section", "schedule", "term", "action")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=16)

    tree.heading("subject_code", text="Subject Code")
    tree.heading("title", text="Descriptive Title")
    tree.heading("section", text="Section")
    tree.heading("schedule", text="Schedule")
    tree.heading("term", text="Term")
    tree.heading("action", text="Action")

    tree.column("subject_code", width=120, anchor="center")
    tree.column("title", width=280, anchor="center")
    tree.column("section", width=120, anchor="center")
    tree.column("schedule", width=180, anchor="center")
    tree.column("term", width=180, anchor="center")
    tree.column("action", width=150, anchor="center")

    y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

    table_frame.rowconfigure(0, weight=1)
    table_frame.columnconfigure(0, weight=1)

    tree.grid(row=0, column=0, sticky="nsew")
    y_scroll.grid(row=0, column=1, sticky="ns")
    x_scroll.grid(row=1, column=0, sticky="ew")

    # ================= STYLE =================
    style = ttk.Style()
    style.theme_use("default")

    style.configure(
        "Treeview",
        background=ROW_WHITE,
        foreground=TEXT_DARK,
        rowheight=38,
        fieldbackground=ROW_WHITE,
        borderwidth=0,
        font=("Segoe UI", 10)
    )

    style.configure(
        "Treeview.Heading",
        font=("Segoe UI", 10, "bold"),
        background="#f3e7e7",
        foreground=TEXT_DARK,
        relief="flat"
    )

    style.map(
        "Treeview",
        background=[("selected", "#eadcdc")],
        foreground=[("selected", TEXT_DARK)]
    )

    tree.tag_configure("evenrow", background=ROW_WHITE)
    tree.tag_configure("oddrow", background=ROW_ALT)

    subject_cache = []
    selected_label_var = tk.StringVar(value="No subject selected")

    bottom_frame = tk.Frame(parent, bg=BG_MAIN)
    bottom_frame.pack(fill="x", pady=(10, 0))

    tk.Label(
        bottom_frame,
        textvariable=selected_label_var,
        font=("Segoe UI", 10),
        bg=BG_MAIN,
        fg=TEXT_MUTED
    ).pack(side="left")

    button_group = tk.Frame(bottom_frame, bg=BG_MAIN)
    button_group.pack(side="right")

    def load_subjects():
        nonlocal subject_cache
        tree.delete(*tree.get_children())

        subject_cache = fetch_subjects_of_faculty_in_period(
            app.active_evaluation_period_id,
            app.selected_faculty_id,
            search_var.get()
        )

        if not subject_cache:
            selected_label_var.set("No subjects found for the selected faculty.")
            return

        for index, row in enumerate(subject_cache):
            row_tag = "evenrow" if index % 2 == 0 else "oddrow"
            section_text = f"Y{row['year_level']}-{row['section_name']}"
            term_text = f"{row['semester']} | {row['school_year']}"

            tree.insert(
                "",
                "end",
                values=(
                    row["subject_code"],
                    row["descriptive_title"],
                    section_text,
                    row["schedule"],
                    term_text,
                    ACTION_TEXT
                ),
                tags=(row_tag,)
            )

        selected_label_var.set("Click [ View Result ] in the Action column.")

    def on_select(event=None):
        selected = tree.selection()
        if not selected:
            selected_label_var.set("No subject selected")
            return

        values = tree.item(selected[0], "values")
        selected_label_var.set(f"Selected Subject: {values[0]} - {values[1]}")

    def on_tree_click(event):
        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        item_id = tree.identify_row(event.y)
        column_id = tree.identify_column(event.x)

        if not item_id:
            return

        tree.selection_set(item_id)
        values = tree.item(item_id, "values")

        # Action column = #6
        if column_id == "#6":
            open_result_from_values(values)

    def on_tree_double_click(event):
        item_id = tree.identify_row(event.y)
        if not item_id:
            return

        values = tree.item(item_id, "values")
        open_result_from_values(values)

    def refresh_data():
        search_var.set("")
        load_subjects()

    def go_back():
        app.show_faculty_page()

    tk.Button(
        button_group,
        text="Back",
        font=("Segoe UI", 10, "bold"),
        bg="#6c757d",
        fg="white",
        activebackground="#5b636a",
        activeforeground="white",
        relief="flat",
        bd=0,
        padx=16,
        pady=8,
        cursor="hand2",
        command=go_back
    ).pack(side="left", padx=(0, 8))

    tk.Button(
        button_group,
        text="Search",
        font=("Segoe UI", 10, "bold"),
        bg=ACCENT,
        fg="white",
        activebackground=ACCENT_HOVER,
        activeforeground="white",
        relief="flat",
        bd=0,
        padx=16,
        pady=8,
        cursor="hand2",
        command=load_subjects
    ).pack(side="left", padx=(0, 8))

    tk.Button(
        button_group,
        text="Refresh",
        font=("Segoe UI", 10, "bold"),
        bg="#6c757d",
        fg="white",
        activebackground="#5b636a",
        activeforeground="white",
        relief="flat",
        bd=0,
        padx=16,
        pady=8,
        cursor="hand2",
        command=refresh_data
    ).pack(side="left")

    search_entry.bind("<Return>", lambda e: load_subjects())
    tree.bind("<<TreeviewSelect>>", on_select)
    tree.bind("<Button-1>", on_tree_click)
    tree.bind("<Double-1>", on_tree_double_click)

    load_subjects()