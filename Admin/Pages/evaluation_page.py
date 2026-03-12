import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, date
from tkcalendar import DateEntry
from db_connection import get_connection

CARD_BG = "#ffffff"
CONTENT_BG = "#fffafa"
TEXT_DARK = "#4a2c2c"
TEXT_MUTED = "#7a5c5c"
ACCENT = "#8b4a4a"
ACCENT_HOVER = "#723939"
BORDER = "#eadede"
ENTRY_BG = "#fffdfd"

ROW_BG_1 = "#ffffff"
ROW_BG_2 = "#fcf7f7"
ROW_HOVER = "#f3e7e7"
ROW_SELECTED = "#ecd9d9"

EDIT_BG = "#8b6a4a"
EDIT_HOVER = "#72553b"

DELETE_BG = "#b23b3b"
DELETE_HOVER = "#d14a4a"

# grid column widths (pixels)
GRID_COLS = {
    0: 60,    # No.
    1: 260,   # Form
    2: 140,   # School Year
    3: 140,   # Semester
    4: 190,   # Start
    5: 190,   # End
    6: 110,   # Status
    7: 170,   # Actions
}


# =========================
# DATABASE FUNCTIONS
# =========================
def fetch_evaluation_forms():
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, title
        FROM evaluation_forms
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def fetch_school_years():
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, year_label
        FROM school_years
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def fetch_semesters():
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, name
        FROM semesters
        ORDER BY id ASC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def fetch_evaluation_periods(search_text=""):
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    base_query = """
        SELECT
            ep.id,
            ep.term_id,
            ep.form_id,
            ep.starts_at,
            ep.ends_at,
            ep.status,
            ef.title AS form_title,
            sy.year_label,
            sem.name AS semester_name
        FROM evaluation_periods ep
        INNER JOIN evaluation_forms ef ON ep.form_id = ef.id
        INNER JOIN terms t ON ep.term_id = t.id
        INNER JOIN school_years sy ON t.school_year_id = sy.id
        INNER JOIN semesters sem ON t.semester_id = sem.id
    """

    if search_text.strip():
        like = f"%{search_text.strip()}%"
        cursor.execute(base_query + """
            WHERE ef.title LIKE %s
               OR sy.year_label LIKE %s
               OR sem.name LIKE %s
               OR ep.status LIKE %s
            ORDER BY ep.id DESC
        """, (like, like, like, like))
    else:
        cursor.execute(base_query + " ORDER BY ep.id DESC")

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_or_create_school_year(year_label):
    conn = get_connection()
    if not conn:
        raise Exception("Could not connect to database.")

    cursor = conn.cursor()
    cursor.execute("SELECT id FROM school_years WHERE year_label = %s", (year_label,))
    row = cursor.fetchone()

    if row:
        school_year_id = row[0]
    else:
        cursor.execute("INSERT INTO school_years (year_label) VALUES (%s)", (year_label,))
        conn.commit()
        school_year_id = cursor.lastrowid

    cursor.close()
    conn.close()
    return school_year_id


def get_or_create_semester(name):
    conn = get_connection()
    if not conn:
        raise Exception("Could not connect to database.")

    cursor = conn.cursor()
    cursor.execute("SELECT id FROM semesters WHERE name = %s", (name,))
    row = cursor.fetchone()

    if row:
        semester_id = row[0]
    else:
        cursor.execute("INSERT INTO semesters (name) VALUES (%s)", (name,))
        conn.commit()
        semester_id = cursor.lastrowid

    cursor.close()
    conn.close()
    return semester_id


def get_or_create_term(school_year_id, semester_id, start_date=None, end_date=None):
    conn = get_connection()
    if not conn:
        raise Exception("Could not connect to database.")

    cursor = conn.cursor()
    cursor.execute("""
        SELECT id
        FROM terms
        WHERE school_year_id = %s AND semester_id = %s
    """, (school_year_id, semester_id))
    row = cursor.fetchone()

    if row:
        term_id = row[0]
        cursor.execute("""
            UPDATE terms
            SET start_date = %s,
                end_date = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (start_date, end_date, term_id))
        conn.commit()
    else:
        cursor.execute("""
            INSERT INTO terms (
                school_year_id, semester_id, start_date, end_date, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (school_year_id, semester_id, start_date, end_date))
        conn.commit()
        term_id = cursor.lastrowid

    cursor.close()
    conn.close()
    return term_id


def insert_evaluation_period(term_id, form_id, starts_at, ends_at, status):
    conn = get_connection()
    if not conn:
        raise Exception("Could not connect to database.")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO evaluation_periods (
            term_id, form_id, starts_at, ends_at, status, created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
    """, (term_id, form_id, starts_at, ends_at, status))
    conn.commit()
    cursor.close()
    conn.close()


def update_evaluation_period(period_id, term_id, form_id, starts_at, ends_at, status):
    conn = get_connection()
    if not conn:
        raise Exception("Could not connect to database.")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE evaluation_periods
        SET term_id = %s,
            form_id = %s,
            starts_at = %s,
            ends_at = %s,
            status = %s,
            updated_at = NOW()
        WHERE id = %s
    """, (term_id, form_id, starts_at, ends_at, status, period_id))
    conn.commit()
    cursor.close()
    conn.close()


def delete_evaluation_period(period_id):
    conn = get_connection()
    if not conn:
        raise Exception("Could not connect to database.")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM evaluation_periods WHERE id = %s", (period_id,))
    conn.commit()
    cursor.close()
    conn.close()


def evaluation_period_has_submissions(period_id):
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM evaluations
        WHERE evaluation_period_id = %s
    """, (period_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] > 0 if row else False


def evaluation_period_duplicate_exists(term_id, form_id, exclude_id=None):
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    if exclude_id is None:
        cursor.execute("""
            SELECT COUNT(*)
            FROM evaluation_periods
            WHERE term_id = %s AND form_id = %s
        """, (term_id, form_id))
    else:
        cursor.execute("""
            SELECT COUNT(*)
            FROM evaluation_periods
            WHERE term_id = %s AND form_id = %s AND id <> %s
        """, (term_id, form_id, exclude_id))

    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] > 0 if row else False


def _configure_table_columns(frame):
    for col, minsize in GRID_COLS.items():
        frame.grid_columnconfigure(col, minsize=minsize)


# =========================
# PAGE
# =========================
def show_evaluation_page(app):
    app.clear_content()
    app.selected_period_id = None
    app.evaluation_rows = []
    app.evaluation_data = []
    app.evaluation_form_map = {}

    if not hasattr(app, "evaluation_search_var"):
        app.evaluation_search_var = tk.StringVar()
    if not hasattr(app, "evaluation_form_var"):
        app.evaluation_form_var = tk.StringVar()
    if not hasattr(app, "evaluation_sy_var"):
        app.evaluation_sy_var = tk.StringVar()
    if not hasattr(app, "evaluation_sem_var"):
        app.evaluation_sem_var = tk.StringVar()
    if not hasattr(app, "evaluation_status_var"):
        app.evaluation_status_var = tk.StringVar()

    wrapper = tk.Frame(app.content_frame, bg=CONTENT_BG)
    wrapper.pack(fill="both", expand=True)

    header_frame = tk.Frame(wrapper, bg=CONTENT_BG)
    header_frame.pack(fill="x", pady=(0, 15))

    left_header = tk.Frame(header_frame, bg=CONTENT_BG)
    left_header.pack(side="left")

    tk.Label(
        left_header,
        text="Evaluation Schedule Management",
        font=("Segoe UI", 18, "bold"),
        fg=TEXT_DARK,
        bg=CONTENT_BG
    ).pack(anchor="w")

    tk.Label(
        left_header,
        text="Create and manage evaluation schedules.",
        font=("Segoe UI", 10),
        fg=TEXT_MUTED,
        bg=CONTENT_BG
    ).pack(anchor="w", pady=(4, 0))

    form_card = tk.Frame(
        wrapper,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=BORDER
    )
    form_card.pack(fill="x", pady=(0, 15))

    tk.Label(
        form_card,
        text="Schedule Details",
        font=("Segoe UI", 13, "bold"),
        fg=TEXT_DARK,
        bg=CARD_BG
    ).grid(row=0, column=0, columnspan=4, sticky="w", padx=20, pady=(18, 15))

    tk.Label(form_card, text="Evaluation Form", font=("Segoe UI", 10, "bold"),
             fg=TEXT_DARK, bg=CARD_BG).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 6))
    app.evaluation_form_combo = ttk.Combobox(
        form_card, textvariable=app.evaluation_form_var, state="readonly", width=28
    )
    app.evaluation_form_combo.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 12), ipady=4)

    tk.Label(form_card, text="School Year", font=("Segoe UI", 10, "bold"),
             fg=TEXT_DARK, bg=CARD_BG).grid(row=1, column=1, sticky="w", padx=20, pady=(0, 6))
    app.evaluation_sy_combo = ttk.Combobox(
        form_card, textvariable=app.evaluation_sy_var, width=18
    )
    app.evaluation_sy_combo.grid(row=2, column=1, sticky="ew", padx=20, pady=(0, 12), ipady=4)

    tk.Label(form_card, text="Semester", font=("Segoe UI", 10, "bold"),
             fg=TEXT_DARK, bg=CARD_BG).grid(row=1, column=2, sticky="w", padx=20, pady=(0, 6))
    app.evaluation_sem_combo = ttk.Combobox(
        form_card, textvariable=app.evaluation_sem_var, width=18
    )
    app.evaluation_sem_combo.grid(row=2, column=2, sticky="ew", padx=20, pady=(0, 12), ipady=4)

    tk.Label(form_card, text="Status", font=("Segoe UI", 10, "bold"),
             fg=TEXT_DARK, bg=CARD_BG).grid(row=1, column=3, sticky="w", padx=20, pady=(0, 6))
    app.evaluation_status_combo = ttk.Combobox(
        form_card, textvariable=app.evaluation_status_var,
        state="readonly", values=["draft", "open", "closed"], width=14
    )
    app.evaluation_status_combo.grid(row=2, column=3, sticky="ew", padx=20, pady=(0, 12), ipady=4)

    tk.Label(form_card, text="Start Date", font=("Segoe UI", 10, "bold"),
             fg=TEXT_DARK, bg=CARD_BG).grid(row=3, column=0, sticky="w", padx=20, pady=(0, 6))
    start_datetime_frame = tk.Frame(form_card, bg=CARD_BG)
    start_datetime_frame.grid(row=4, column=0, sticky="w", padx=20, pady=(0, 12))

    start_date_entry = DateEntry(
        start_datetime_frame,
        width=12,
        font=("Segoe UI", 10),
        date_pattern="yyyy-mm-dd",
        background=ACCENT,
        foreground="white",
        borderwidth=1,
        mindate=date.today()
    )
    start_date_entry.pack(side="left", padx=(0, 14), ipady=4)

    start_hour_var = tk.StringVar(value="08")
    start_minute_var = tk.StringVar(value="00")
    start_second_var = tk.StringVar(value="00")

    ttk.Combobox(start_datetime_frame, textvariable=start_hour_var,
                 values=[f"{i:02d}" for i in range(24)], state="readonly", width=3).pack(side="left")
    tk.Label(start_datetime_frame, text=":", bg=CARD_BG, fg=TEXT_DARK,
             font=("Segoe UI", 10, "bold")).pack(side="left", padx=2)
    ttk.Combobox(start_datetime_frame, textvariable=start_minute_var,
                 values=[f"{i:02d}" for i in range(60)], state="readonly", width=3).pack(side="left")
    tk.Label(start_datetime_frame, text=":", bg=CARD_BG, fg=TEXT_DARK,
             font=("Segoe UI", 10, "bold")).pack(side="left", padx=2)
    ttk.Combobox(start_datetime_frame, textvariable=start_second_var,
                 values=[f"{i:02d}" for i in range(60)], state="readonly", width=3).pack(side="left")

    tk.Label(form_card, text="End Date", font=("Segoe UI", 10, "bold"),
             fg=TEXT_DARK, bg=CARD_BG).grid(row=3, column=1, sticky="w", padx=20, pady=(0, 6))
    end_datetime_frame = tk.Frame(form_card, bg=CARD_BG)
    end_datetime_frame.grid(row=4, column=1, sticky="w", padx=20, pady=(0, 12))

    end_date_entry = DateEntry(
        end_datetime_frame,
        width=12,
        font=("Segoe UI", 10),
        date_pattern="yyyy-mm-dd",
        background=ACCENT,
        foreground="white",
        borderwidth=1,
        mindate=date.today()
    )
    end_date_entry.pack(side="left", padx=(0, 14), ipady=4)

    end_hour_var = tk.StringVar(value="17")
    end_minute_var = tk.StringVar(value="00")
    end_second_var = tk.StringVar(value="00")

    ttk.Combobox(end_datetime_frame, textvariable=end_hour_var,
                 values=[f"{i:02d}" for i in range(24)], state="readonly", width=3).pack(side="left")
    tk.Label(end_datetime_frame, text=":", bg=CARD_BG, fg=TEXT_DARK,
             font=("Segoe UI", 10, "bold")).pack(side="left", padx=2)
    ttk.Combobox(end_datetime_frame, textvariable=end_minute_var,
                 values=[f"{i:02d}" for i in range(60)], state="readonly", width=3).pack(side="left")
    tk.Label(end_datetime_frame, text=":", bg=CARD_BG, fg=TEXT_DARK,
             font=("Segoe UI", 10, "bold")).pack(side="left", padx=2)
    ttk.Combobox(end_datetime_frame, textvariable=end_second_var,
                 values=[f"{i:02d}" for i in range(60)], state="readonly", width=3).pack(side="left")

    tk.Label(
        form_card,
        text="Pick the date from the calendar, then choose the time.",
        font=("Segoe UI", 9),
        fg=TEXT_MUTED,
        bg=CARD_BG
    ).grid(row=5, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 16))

    button_frame = tk.Frame(form_card, bg=CARD_BG)
    button_frame.grid(row=4, column=2, columnspan=2, sticky="e", padx=20)

    bottom_top = tk.Frame(wrapper, bg=CONTENT_BG)
    bottom_top.pack(fill="x", pady=(0, 10))

    app.evaluation_search_var.set("")
    search_entry = tk.Entry(
        bottom_top,
        textvariable=app.evaluation_search_var,
        font=("Segoe UI", 10),
        bg=ENTRY_BG,
        fg=TEXT_DARK,
        relief="solid",
        bd=1,
        width=35
    )
    search_entry.pack(side="right", ipady=5)

    table_card = tk.Frame(
        wrapper,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=BORDER
    )
    table_card.pack(fill="both", expand=True)

    top_info = tk.Frame(table_card, bg=CARD_BG)
    top_info.pack(fill="x", padx=18, pady=(16, 10))

    app.evaluation_count_label = tk.Label(
        top_info,
        text="0 schedules found",
        font=("Segoe UI", 10),
        fg=TEXT_MUTED,
        bg=CARD_BG
    )
    app.evaluation_count_label.pack(side="left")

    header_row = tk.Frame(table_card, bg="#f4ebeb", height=44)
    header_row.pack(fill="x", padx=18)
    header_row.pack_propagate(False)
    _configure_table_columns(header_row)

    header_labels = [
        ("No.", 0, "center"),
        ("Form", 1, "w"),
        ("School Year", 2, "center"),
        ("Semester", 3, "center"),
        ("Start", 4, "center"),
        ("End", 5, "center"),
        ("Status", 6, "center"),
        ("Actions", 7, "center"),
    ]

    for text, col, anchor in header_labels:
        tk.Label(
            header_row,
            text=text,
            font=("Segoe UI", 10, "bold"),
            fg=TEXT_DARK,
            bg="#f4ebeb",
            anchor=anchor
        ).grid(row=0, column=col, sticky="nsew", padx=4, pady=10)

    list_container = tk.Frame(table_card, bg=CARD_BG)
    list_container.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    app.evaluation_canvas = tk.Canvas(list_container, bg=CARD_BG, highlightthickness=0)
    app.evaluation_canvas.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(list_container, orient="vertical", command=app.evaluation_canvas.yview)
    scrollbar.pack(side="right", fill="y")

    app.evaluation_canvas.configure(yscrollcommand=scrollbar.set)
    app.evaluation_list_frame = tk.Frame(app.evaluation_canvas, bg=CARD_BG)

    app.evaluation_canvas_window = app.evaluation_canvas.create_window(
        (0, 0), window=app.evaluation_list_frame, anchor="nw"
    )

    app.evaluation_list_frame.bind(
        "<Configure>",
        lambda e: app.evaluation_canvas.configure(scrollregion=app.evaluation_canvas.bbox("all"))
    )
    app.evaluation_canvas.bind(
        "<Configure>",
        lambda e: app.evaluation_canvas.itemconfig(app.evaluation_canvas_window, width=e.width)
    )

    app.evaluation_canvas.bind("<Enter>", lambda e: _bind_mousewheel(app))
    app.evaluation_canvas.bind("<Leave>", lambda e: _unbind_mousewheel(app))
    app.evaluation_search_var.trace_add("write", lambda *args: refresh_evaluation_data(app))

    def update_end_min_date(event=None):
        start_selected_date = start_date_entry.get_date()
        end_date_entry.config(mindate=start_selected_date)
        if end_date_entry.get_date() < start_selected_date:
            end_date_entry.set_date(start_selected_date)

    start_date_entry.bind("<<DateEntrySelected>>", update_end_min_date)

    def load_form_options():
        forms = fetch_evaluation_forms()
        app.evaluation_form_map = {item["title"]: item["id"] for item in forms}
        titles = list(app.evaluation_form_map.keys())
        app.evaluation_form_combo["values"] = titles
        if titles:
            if app.evaluation_form_var.get().strip() not in titles:
                app.evaluation_form_var.set(titles[0])
        else:
            app.evaluation_form_var.set("")

    def load_school_year_options():
        years = fetch_school_years()
        year_labels = [item["year_label"] for item in years]
        if "2025-2026" not in year_labels:
            year_labels.insert(0, "2025-2026")
        app.evaluation_sy_combo["values"] = year_labels
        if year_labels and not app.evaluation_sy_var.get().strip():
            app.evaluation_sy_var.set(year_labels[0])

    def load_semester_options():
        sems = fetch_semesters()
        sem_names = [item["name"] for item in sems]
        if not sem_names:
            sem_names = ["1st Semester", "2nd Semester", "Summer"]
        app.evaluation_sem_combo["values"] = sem_names
        if sem_names and not app.evaluation_sem_var.get().strip():
            app.evaluation_sem_var.set(sem_names[0])

    def clear_form():
        app.selected_period_id = None
        load_form_options()
        load_school_year_options()
        load_semester_options()
        app.evaluation_status_var.set("draft")

        start_date_entry.set_date(date.today())
        end_date_entry.set_date(date.today())
        end_date_entry.config(mindate=date.today())

        start_hour_var.set("08")
        start_minute_var.set("00")
        start_second_var.set("00")

        end_hour_var.set("17")
        end_minute_var.set("00")
        end_second_var.set("00")

        save_btn.config(text="Save Schedule")

    def get_selected_form_id():
        selected_title = app.evaluation_form_var.get().strip()
        return app.evaluation_form_map.get(selected_title)

    def save_schedule():
        form_id = get_selected_form_id()
        year_label = app.evaluation_sy_var.get().strip()
        semester_name = app.evaluation_sem_var.get().strip()
        status = app.evaluation_status_var.get().strip()

        if not form_id:
            messagebox.showwarning("Missing Field", "Please select an evaluation form.")
            return
        if not year_label:
            messagebox.showwarning("Missing Field", "Please enter a school year.")
            return
        if not semester_name:
            messagebox.showwarning("Missing Field", "Please enter a semester.")
            return
        if not status:
            messagebox.showwarning("Missing Field", "Please select a status.")
            return

        start_date_text = start_date_entry.get_date().strftime("%Y-%m-%d")
        end_date_text = end_date_entry.get_date().strftime("%Y-%m-%d")

        starts_at_text = f"{start_date_text} {start_hour_var.get()}:{start_minute_var.get()}:{start_second_var.get()}"
        ends_at_text = f"{end_date_text} {end_hour_var.get()}:{end_minute_var.get()}:{end_second_var.get()}"

        try:
            start_dt = datetime.strptime(starts_at_text, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(ends_at_text, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            messagebox.showwarning("Invalid Date", "Invalid date or time selection.")
            return

        if start_dt >= end_dt:
            messagebox.showwarning("Invalid Range", "End date and time must be greater than start date and time.")
            return
        if start_dt.date() < date.today():
            messagebox.showwarning("Invalid Start Date", "You cannot select an old start date.")
            return
        if end_dt.date() < date.today():
            messagebox.showwarning("Invalid End Date", "You cannot select an old end date.")
            return

        try:
            school_year_id = get_or_create_school_year(year_label)
            semester_id = get_or_create_semester(semester_name)
            term_id = get_or_create_term(
                school_year_id,
                semester_id,
                start_dt.date(),
                end_dt.date()
            )

            if evaluation_period_duplicate_exists(term_id, form_id, app.selected_period_id):
                messagebox.showwarning(
                    "Duplicate Schedule",
                    "This evaluation form already has a schedule for the selected school year and semester."
                )
                return

            if app.selected_period_id is None:
                insert_evaluation_period(term_id, form_id, starts_at_text, ends_at_text, status)
                messagebox.showinfo("Success", "Evaluation schedule added successfully.")
            else:
                update_evaluation_period(
                    app.selected_period_id,
                    term_id,
                    form_id,
                    starts_at_text,
                    ends_at_text,
                    status
                )
                messagebox.showinfo("Updated", "Evaluation schedule updated successfully.")

            clear_form()
            refresh_evaluation_data(app)

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def open_selected_for_edit(period_id=None):
        if period_id is not None:
            app.selected_period_id = period_id

        if app.selected_period_id is None:
            messagebox.showwarning("No Selection", "Please select a schedule to edit.")
            return

        selected = next((item for item in app.evaluation_data if item["id"] == app.selected_period_id), None)
        if not selected:
            return

        app.evaluation_form_var.set(selected["form_title"])
        app.evaluation_sy_var.set(selected["year_label"])
        app.evaluation_sem_var.set(selected["semester_name"])
        app.evaluation_status_var.set(selected["status"])

        start_value = selected["starts_at"]
        end_value = selected["ends_at"]

        start_dt = datetime.strptime(start_value, "%Y-%m-%d %H:%M:%S") if isinstance(start_value, str) else start_value
        end_dt = datetime.strptime(end_value, "%Y-%m-%d %H:%M:%S") if isinstance(end_value, str) else end_value

        start_date_entry.set_date(start_dt.date())
        start_hour_var.set(f"{start_dt.hour:02d}")
        start_minute_var.set(f"{start_dt.minute:02d}")
        start_second_var.set(f"{start_dt.second:02d}")

        end_date_entry.set_date(end_dt.date())
        end_hour_var.set(f"{end_dt.hour:02d}")
        end_minute_var.set(f"{end_dt.minute:02d}")
        end_second_var.set(f"{end_dt.second:02d}")

        end_date_entry.config(mindate=start_dt.date())
        save_btn.config(text="Update Schedule")

    def delete_selected(period_id=None):
        if period_id is not None:
            app.selected_period_id = period_id

        if app.selected_period_id is None:
            messagebox.showwarning("No Selection", "Please select a schedule to delete.")
            return

        if evaluation_period_has_submissions(app.selected_period_id):
            messagebox.showwarning(
                "Cannot Delete",
                "This schedule cannot be deleted because it already has evaluation submissions."
            )
            return

        confirm = messagebox.askyesno(
            "Delete Schedule",
            "Are you sure you want to delete the selected evaluation schedule?"
        )
        if confirm:
            try:
                delete_evaluation_period(app.selected_period_id)
                app.selected_period_id = None
                clear_form()
                refresh_evaluation_data(app)
                messagebox.showinfo("Deleted", "Evaluation schedule deleted successfully.")
            except Exception as e:
                messagebox.showerror("Database Error", str(e))

    save_btn = tk.Button(
        button_frame,
        text="Save Schedule",
        font=("Segoe UI", 10, "bold"),
        bg=ACCENT,
        fg="white",
        activebackground=ACCENT_HOVER,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        width=14,
        command=save_schedule
    )
    save_btn.pack(side="left", padx=(0, 8), ipady=4)

    clear_btn = tk.Button(
        button_frame,
        text="Clear",
        font=("Segoe UI", 10, "bold"),
        bg="#ddd0d0",
        fg=TEXT_DARK,
        activebackground="#ccbaba",
        activeforeground=TEXT_DARK,
        relief="flat",
        bd=0,
        cursor="hand2",
        width=12,
        command=clear_form
    )
    clear_btn.pack(side="left", ipady=4)

    app._edit_evaluation_period = open_selected_for_edit
    app._delete_evaluation_period = delete_selected

    load_form_options()
    load_school_year_options()
    load_semester_options()
    clear_form()
    refresh_evaluation_data(app)


def _bind_mousewheel(app):
    app.root.bind_all("<MouseWheel>", lambda event: _on_mousewheel(app, event))


def _unbind_mousewheel(app):
    app.root.unbind_all("<MouseWheel>")


def _on_mousewheel(app, event):
    if hasattr(app, "evaluation_canvas") and app.evaluation_canvas.winfo_exists():
        app.evaluation_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


def refresh_evaluation_data(app):
    search_text = app.evaluation_search_var.get().strip()
    app.evaluation_data = fetch_evaluation_periods(search_text)
    app.selected_period_id = None
    render_evaluation_rows(app)


def render_evaluation_rows(app):
    if not hasattr(app, "evaluation_list_frame") or not app.evaluation_list_frame.winfo_exists():
        return

    for widget in app.evaluation_list_frame.winfo_children():
        widget.destroy()

    app.evaluation_rows = []
    count = len(app.evaluation_data)

    if hasattr(app, "evaluation_count_label") and app.evaluation_count_label.winfo_exists():
        app.evaluation_count_label.config(text=f"{count} schedules found")

    if not app.evaluation_data:
        empty_box = tk.Frame(app.evaluation_list_frame, bg=CARD_BG)
        empty_box.pack(fill="both", expand=True, pady=50)

        tk.Label(
            empty_box,
            text="No evaluation schedules found",
            font=("Segoe UI", 15, "bold"),
            fg=TEXT_DARK,
            bg=CARD_BG
        ).pack(pady=(0, 8))

        tk.Label(
            empty_box,
            text="Add a new schedule to begin managing evaluation periods.",
            font=("Segoe UI", 11),
            fg=TEXT_MUTED,
            bg=CARD_BG
        ).pack()

        app.evaluation_list_frame.update_idletasks()
        app.evaluation_canvas.configure(scrollregion=app.evaluation_canvas.bbox("all"))
        return

    for display_index, item in enumerate(app.evaluation_data):
        period_id = item["id"]
        base_bg = ROW_BG_1 if display_index % 2 == 0 else ROW_BG_2

        row = tk.Frame(
            app.evaluation_list_frame,
            bg=base_bg,
            height=60,
            highlightthickness=1,
            highlightbackground="#efe3e3"
        )
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        _configure_table_columns(row)

        no_label = tk.Label(row, text=str(display_index + 1), font=("Segoe UI", 10),
                            fg=TEXT_DARK, bg=base_bg, anchor="center")
        no_label.grid(row=0, column=0, sticky="nsew", padx=4, pady=10)

        form_label = tk.Label(row, text=item["form_title"], font=("Segoe UI", 10, "bold"),
                              fg=TEXT_DARK, bg=base_bg, anchor="w")
        form_label.grid(row=0, column=1, sticky="nsew", padx=4, pady=10)

        sy_label = tk.Label(row, text=item["year_label"], font=("Segoe UI", 10),
                            fg=TEXT_DARK, bg=base_bg, anchor="center")
        sy_label.grid(row=0, column=2, sticky="nsew", padx=4, pady=10)

        sem_label = tk.Label(row, text=item["semester_name"], font=("Segoe UI", 10),
                             fg=TEXT_DARK, bg=base_bg, anchor="center")
        sem_label.grid(row=0, column=3, sticky="nsew", padx=4, pady=10)

        start_label = tk.Label(row, text=str(item["starts_at"]), font=("Segoe UI", 9),
                               fg=TEXT_MUTED, bg=base_bg, anchor="center")
        start_label.grid(row=0, column=4, sticky="nsew", padx=4, pady=10)

        end_label = tk.Label(row, text=str(item["ends_at"]), font=("Segoe UI", 9),
                             fg=TEXT_MUTED, bg=base_bg, anchor="center")
        end_label.grid(row=0, column=5, sticky="nsew", padx=4, pady=10)

        status_fg = {
            "draft": "#8d6e63",
            "open": "#2e7d32",
            "closed": "#c62828"
        }.get(item["status"], TEXT_DARK)

        status_label = tk.Label(row, text=item["status"].capitalize(), font=("Segoe UI", 10, "bold"),
                                fg=status_fg, bg=base_bg, anchor="center")
        status_label.grid(row=0, column=6, sticky="nsew", padx=4, pady=10)

        action_frame = tk.Frame(row, bg=base_bg)
        action_frame.grid(row=0, column=7, sticky="nsew", padx=8, pady=10)

        edit_btn = tk.Label(
            action_frame, text="Edit", font=("Segoe UI", 9, "bold"),
            fg="white", bg=EDIT_BG, padx=12, pady=5, cursor="hand2"
        )
        edit_btn.pack(side="left", padx=(0, 6))

        delete_btn = tk.Label(
            action_frame, text="Delete", font=("Segoe UI", 9, "bold"),
            fg="white", bg=DELETE_BG, padx=12, pady=5, cursor="hand2"
        )
        delete_btn.pack(side="left")

        row_data = {
            "frame": row,
            "no": no_label,
            "form": form_label,
            "sy": sy_label,
            "sem": sem_label,
            "start": start_label,
            "end": end_label,
            "status": status_label,
            "action_frame": action_frame,
            "edit": edit_btn,
            "delete": delete_btn,
            "base_bg": base_bg,
            "period_id": period_id
        }
        app.evaluation_rows.append(row_data)

        def select_row(event, pid=period_id):
            app.selected_period_id = pid
            refresh_evaluation_row_states(app)

        def hover_in(event, pid=period_id):
            if app.selected_period_id != pid:
                set_evaluation_row_bg(app, pid, ROW_HOVER)

        def hover_out(event, pid=period_id, bg=base_bg):
            if app.selected_period_id != pid:
                set_evaluation_row_bg(app, pid, bg)

        for widget in [row, no_label, form_label, sy_label, sem_label, start_label, end_label, status_label, action_frame]:
            widget.bind("<Button-1>", select_row)
            widget.bind("<Enter>", hover_in)
            widget.bind("<Leave>", hover_out)

        edit_btn.bind("<Enter>", lambda e, btn=edit_btn: btn.config(bg=EDIT_HOVER))
        edit_btn.bind("<Leave>", lambda e, btn=edit_btn: btn.config(bg=EDIT_BG))
        edit_btn.bind("<Button-1>", lambda e, pid=period_id: app._edit_evaluation_period(pid))

        delete_btn.bind("<Enter>", lambda e, btn=delete_btn: btn.config(bg=DELETE_HOVER))
        delete_btn.bind("<Leave>", lambda e, btn=delete_btn: btn.config(bg=DELETE_BG))
        delete_btn.bind("<Button-1>", lambda e, pid=period_id: app._delete_evaluation_period(pid))

    refresh_evaluation_row_states(app)
    app.evaluation_list_frame.update_idletasks()
    app.evaluation_canvas.configure(scrollregion=app.evaluation_canvas.bbox("all"))


def set_evaluation_row_bg(app, period_id, color):
    for row_data in app.evaluation_rows:
        if row_data["period_id"] == period_id:
            row_data["frame"].config(bg=color)
            row_data["no"].config(bg=color)
            row_data["form"].config(bg=color)
            row_data["sy"].config(bg=color)
            row_data["sem"].config(bg=color)
            row_data["start"].config(bg=color)
            row_data["end"].config(bg=color)
            row_data["status"].config(bg=color)
            row_data["action_frame"].config(bg=color)
            break


def refresh_evaluation_row_states(app):
    for row_data in app.evaluation_rows:
        bg = ROW_SELECTED if row_data["period_id"] == app.selected_period_id else row_data["base_bg"]
        row_data["frame"].config(bg=bg)
        row_data["no"].config(bg=bg)
        row_data["form"].config(bg=bg)
        row_data["sy"].config(bg=bg)
        row_data["sem"].config(bg=bg)
        row_data["start"].config(bg=bg)
        row_data["end"].config(bg=bg)
        row_data["status"].config(bg=bg)
        row_data["action_frame"].config(bg=bg)