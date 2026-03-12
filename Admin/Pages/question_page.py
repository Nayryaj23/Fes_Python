import tkinter as tk
from tkinter import messagebox, ttk
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

TAG_BG = "#efe2e2"


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


def fetch_criteria_by_form(form_id):
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, title, description, position
        FROM criteria
        WHERE form_id = %s
        ORDER BY position ASC, id ASC
    """, (form_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def fetch_questions_by_criterion(criterion_id, search_text=""):
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    if search_text.strip():
        like = f"%{search_text.strip()}%"
        cursor.execute("""
            SELECT 
                cq.id AS criterion_question_id,
                cq.criterion_id,
                cq.question_id,
                cq.position,
                cq.is_required,
                q.question_text,
                q.is_active
            FROM criterion_questions cq
            INNER JOIN questions q ON cq.question_id = q.id
            WHERE cq.criterion_id = %s
              AND q.question_text LIKE %s
            ORDER BY cq.position ASC, cq.id ASC
        """, (criterion_id, like))
    else:
        cursor.execute("""
            SELECT 
                cq.id AS criterion_question_id,
                cq.criterion_id,
                cq.question_id,
                cq.position,
                cq.is_required,
                q.question_text,
                q.is_active
            FROM criterion_questions cq
            INNER JOIN questions q ON cq.question_id = q.id
            WHERE cq.criterion_id = %s
            ORDER BY cq.position ASC, cq.id ASC
        """, (criterion_id,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_next_question_position(criterion_id):
    conn = get_connection()
    if not conn:
        return 1

    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(MAX(position), 0) + 1
        FROM criterion_questions
        WHERE criterion_id = %s
    """, (criterion_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else 1


def insert_question_with_link(criterion_id, question_text, is_required=1):
    conn = get_connection()
    if not conn:
        raise Exception("Could not connect to database.")

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO questions (question_text, is_active, created_at, updated_at)
        VALUES (%s, 1, NOW(), NOW())
    """, (question_text,))
    question_id = cursor.lastrowid

    next_position = get_next_question_position(criterion_id)

    cursor.execute("""
        INSERT INTO criterion_questions (
            criterion_id, question_id, position, is_required, created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, NOW(), NOW())
    """, (criterion_id, question_id, next_position, is_required))

    conn.commit()
    cursor.close()
    conn.close()


def update_question_and_link(criterion_question_id, question_id, question_text, is_required):
    conn = get_connection()
    if not conn:
        raise Exception("Could not connect to database.")

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE questions
        SET question_text = %s,
            updated_at = NOW()
        WHERE id = %s
    """, (question_text, question_id))

    cursor.execute("""
        UPDATE criterion_questions
        SET is_required = %s,
            updated_at = NOW()
        WHERE id = %s
    """, (is_required, criterion_question_id))

    conn.commit()
    cursor.close()
    conn.close()


def delete_criterion_question_link(criterion_question_id):
    conn = get_connection()
    if not conn:
        raise Exception("Could not connect to database.")

    cursor = conn.cursor()
    cursor.execute("DELETE FROM criterion_questions WHERE id = %s", (criterion_question_id,))
    conn.commit()
    cursor.close()
    conn.close()


def question_is_used_in_answers(criterion_question_id):
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM evaluation_answers
        WHERE criterion_question_id = %s
    """, (criterion_question_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] > 0 if row else False


def question_text_exists_under_criterion(criterion_id, question_text, exclude_question_id=None):
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    if exclude_question_id is None:
        cursor.execute("""
            SELECT COUNT(*)
            FROM criterion_questions cq
            INNER JOIN questions q ON cq.question_id = q.id
            WHERE cq.criterion_id = %s
              AND LOWER(TRIM(q.question_text)) = LOWER(TRIM(%s))
        """, (criterion_id, question_text))
    else:
        cursor.execute("""
            SELECT COUNT(*)
            FROM criterion_questions cq
            INNER JOIN questions q ON cq.question_id = q.id
            WHERE cq.criterion_id = %s
              AND LOWER(TRIM(q.question_text)) = LOWER(TRIM(%s))
              AND q.id <> %s
        """, (criterion_id, question_text, exclude_question_id))

    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] > 0 if row else False


# =========================
# PAGE
# =========================
def show_question_page(app):
    app.clear_content()
    app.selected_question_link_id = None
    app.question_rows = []
    app.question_data = []
    app.question_form_map = {}
    app.question_criterion_map = {}

    if not hasattr(app, "question_search_var"):
        app.question_search_var = tk.StringVar()

    if not hasattr(app, "question_form_var"):
        app.question_form_var = tk.StringVar()

    if not hasattr(app, "question_criterion_var"):
        app.question_criterion_var = tk.StringVar()

    app.question_search_var.set("")

    wrapper = tk.Frame(app.content_frame, bg=CONTENT_BG)
    wrapper.pack(fill="both", expand=True)

    # Header
    header_frame = tk.Frame(wrapper, bg=CONTENT_BG)
    header_frame.pack(fill="x", pady=(0, 15))

    left_header = tk.Frame(header_frame, bg=CONTENT_BG)
    left_header.pack(side="left")

    tk.Label(
        left_header,
        text="Question Management",
        font=("Segoe UI", 18, "bold"),
        fg=TEXT_DARK,
        bg=CONTENT_BG
    ).pack(anchor="w")

    tk.Label(
        left_header,
        text="Manage questions under the selected evaluation form and criterion.",
        font=("Segoe UI", 10),
        fg=TEXT_MUTED,
        bg=CONTENT_BG
    ).pack(anchor="w", pady=(4, 0))

    right_header = tk.Frame(header_frame, bg=CONTENT_BG)
    right_header.pack(side="right")

    app.question_form_combo = ttk.Combobox(
        right_header,
        textvariable=app.question_form_var,
        state="readonly",
        width=24
    )
    app.question_form_combo.pack(side="left", padx=(0, 10), ipady=4)
    app.question_form_combo.bind("<<ComboboxSelected>>", lambda e: on_form_change(app))

    app.question_criterion_combo = ttk.Combobox(
        right_header,
        textvariable=app.question_criterion_var,
        state="readonly",
        width=24
    )
    app.question_criterion_combo.pack(side="left", padx=(0, 10), ipady=4)
    app.question_criterion_combo.bind("<<ComboboxSelected>>", lambda e: refresh_question_data(app))

    search_entry = tk.Entry(
        right_header,
        textvariable=app.question_search_var,
        font=("Segoe UI", 10),
        bg=ENTRY_BG,
        fg=TEXT_DARK,
        relief="solid",
        bd=1,
        width=26
    )
    search_entry.pack(side="left", padx=(0, 10), ipady=5)

    add_btn = tk.Button(
        right_header,
        text="+ Add Question",
        font=("Segoe UI", 10, "bold"),
        bg=ACCENT,
        fg="white",
        activebackground=ACCENT_HOVER,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=16,
        pady=8,
        command=lambda: open_add_question_modal(app)
    )
    add_btn.pack(side="left")

    # Table card
    table_card = tk.Frame(
        wrapper,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=BORDER
    )
    table_card.pack(fill="both", expand=True)

    top_info = tk.Frame(table_card, bg=CARD_BG)
    top_info.pack(fill="x", padx=18, pady=(16, 10))

    app.question_count_label = tk.Label(
        top_info,
        text="0 questions found",
        font=("Segoe UI", 10),
        fg=TEXT_MUTED,
        bg=CARD_BG
    )
    app.question_count_label.pack(side="left")

    # Header row
    header_row = tk.Frame(table_card, bg="#f4ebeb", height=44)
    header_row.pack(fill="x", padx=18)
    header_row.pack_propagate(False)

    tk.Label(
        header_row,
        text="No.",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="#f4ebeb",
        width=6,
        anchor="center"
    ).pack(side="left")

    tk.Label(
        header_row,
        text="Question",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="#f4ebeb",
        anchor="w"
    ).pack(side="left", fill="x", expand=True)

    tk.Label(
        header_row,
        text="Required",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="#f4ebeb",
        width=12,
        anchor="center"
    ).pack(side="left", padx=(10, 0))

    tk.Label(
        header_row,
        text="Actions",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="#f4ebeb",
        width=18,
        anchor="center"
    ).pack(side="right", padx=(10, 10))

    # Scrollable list
    list_container = tk.Frame(table_card, bg=CARD_BG)
    list_container.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    app.question_canvas = tk.Canvas(list_container, bg=CARD_BG, highlightthickness=0)
    app.question_canvas.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(list_container, orient="vertical", command=app.question_canvas.yview)
    scrollbar.pack(side="right", fill="y")

    app.question_canvas.configure(yscrollcommand=scrollbar.set)

    app.question_list_frame = tk.Frame(app.question_canvas, bg=CARD_BG)

    app.question_canvas_window = app.question_canvas.create_window(
        (0, 0),
        window=app.question_list_frame,
        anchor="nw"
    )

    app.question_list_frame.bind(
        "<Configure>",
        lambda e: app.question_canvas.configure(scrollregion=app.question_canvas.bbox("all"))
    )

    app.question_canvas.bind(
        "<Configure>",
        lambda e: app.question_canvas.itemconfig(app.question_canvas_window, width=e.width)
    )

    app.question_search_var.trace_add("write", lambda *args: _on_question_search_change(app))

    app.question_canvas.bind("<Enter>", lambda e: _bind_mousewheel(app))
    app.question_canvas.bind("<Leave>", lambda e: _unbind_mousewheel(app))

    load_question_forms(app)
    on_form_change(app)


def _bind_mousewheel(app):
    app.root.bind_all("<MouseWheel>", lambda event: _on_mousewheel(app, event))


def _unbind_mousewheel(app):
    app.root.unbind_all("<MouseWheel>")


def _on_mousewheel(app, event):
    if hasattr(app, "question_canvas") and app.question_canvas.winfo_exists():
        app.question_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


def _on_question_search_change(app):
    if hasattr(app, "question_list_frame") and app.question_list_frame.winfo_exists():
        refresh_question_data(app)


def load_question_forms(app):
    forms = fetch_evaluation_forms()
    app.question_form_map = {form["title"]: form["id"] for form in forms}

    titles = list(app.question_form_map.keys())
    app.question_form_combo["values"] = titles

    if titles:
        app.question_form_var.set(titles[0])
    else:
        app.question_form_var.set("")


def get_selected_question_form_id(app):
    selected_title = app.question_form_var.get().strip()
    return app.question_form_map.get(selected_title)


def load_criteria_for_question_page(app):
    form_id = get_selected_question_form_id(app)

    if not form_id:
        app.question_criterion_map = {}
        app.question_criterion_combo["values"] = []
        app.question_criterion_var.set("")
        return

    criteria = fetch_criteria_by_form(form_id)
    app.question_criterion_map = {criterion["title"]: criterion["id"] for criterion in criteria}

    criterion_titles = list(app.question_criterion_map.keys())
    app.question_criterion_combo["values"] = criterion_titles

    if criterion_titles:
        app.question_criterion_var.set(criterion_titles[0])
    else:
        app.question_criterion_var.set("")


def get_selected_criterion_id(app):
    selected_title = app.question_criterion_var.get().strip()
    return app.question_criterion_map.get(selected_title)


def on_form_change(app):
    load_criteria_for_question_page(app)
    refresh_question_data(app)


def refresh_question_data(app):
    criterion_id = get_selected_criterion_id(app)

    if not criterion_id:
        app.question_data = []
        app.selected_question_link_id = None
        render_question_rows(app)
        return

    search_text = app.question_search_var.get().strip()
    app.question_data = fetch_questions_by_criterion(criterion_id, search_text)
    app.selected_question_link_id = None
    render_question_rows(app)


def render_question_rows(app):
    if not hasattr(app, "question_list_frame") or not app.question_list_frame.winfo_exists():
        return

    for widget in app.question_list_frame.winfo_children():
        widget.destroy()

    app.question_rows = []
    count = len(app.question_data)

    if hasattr(app, "question_count_label") and app.question_count_label.winfo_exists():
        app.question_count_label.config(text=f"{count} questions found")

    if not app.question_form_var.get().strip():
        empty_box = tk.Frame(app.question_list_frame, bg=CARD_BG)
        empty_box.pack(fill="both", expand=True, pady=50)

        tk.Label(
            empty_box,
            text="No evaluation form found",
            font=("Segoe UI", 15, "bold"),
            fg=TEXT_DARK,
            bg=CARD_BG
        ).pack(pady=(0, 8))

        tk.Label(
            empty_box,
            text="Please create an evaluation form first.",
            font=("Segoe UI", 11),
            fg=TEXT_MUTED,
            bg=CARD_BG
        ).pack()
        return

    if not app.question_criterion_var.get().strip():
        empty_box = tk.Frame(app.question_list_frame, bg=CARD_BG)
        empty_box.pack(fill="both", expand=True, pady=50)

        tk.Label(
            empty_box,
            text="No criterion found",
            font=("Segoe UI", 15, "bold"),
            fg=TEXT_DARK,
            bg=CARD_BG
        ).pack(pady=(0, 8))

        tk.Label(
            empty_box,
            text="Please create a criterion first for the selected form.",
            font=("Segoe UI", 11),
            fg=TEXT_MUTED,
            bg=CARD_BG
        ).pack()
        return

    if not app.question_data:
        empty_box = tk.Frame(app.question_list_frame, bg=CARD_BG)
        empty_box.pack(fill="both", expand=True, pady=50)

        tk.Label(
            empty_box,
            text="No questions found",
            font=("Segoe UI", 15, "bold"),
            fg=TEXT_DARK,
            bg=CARD_BG
        ).pack(pady=(0, 8))

        tk.Label(
            empty_box,
            text="Try a different search or add a new question.",
            font=("Segoe UI", 11),
            fg=TEXT_MUTED,
            bg=CARD_BG
        ).pack()

        app.question_list_frame.update_idletasks()
        app.question_canvas.configure(scrollregion=app.question_canvas.bbox("all"))
        return

    for display_index, item in enumerate(app.question_data):
        criterion_question_id = item["criterion_question_id"]
        base_bg = ROW_BG_1 if display_index % 2 == 0 else ROW_BG_2

        row = tk.Frame(
            app.question_list_frame,
            bg=base_bg,
            height=62,
            highlightthickness=1,
            highlightbackground="#efe3e3"
        )
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        no_label = tk.Label(
            row,
            text=str(display_index + 1),
            font=("Segoe UI", 10),
            fg=TEXT_DARK,
            bg=base_bg,
            width=6,
            anchor="center"
        )
        no_label.pack(side="left")

        question_label = tk.Label(
            row,
            text=item["question_text"],
            font=("Segoe UI", 10),
            fg=TEXT_DARK,
            bg=base_bg,
            anchor="w",
            justify="left",
            wraplength=620
        )
        question_label.pack(side="left", fill="x", expand=True, padx=(0, 10))

        required_text = "Yes" if int(item["is_required"]) == 1 else "No"
        required_fg = "#2e7d32" if int(item["is_required"]) == 1 else "#8d6e63"

        required_label = tk.Label(
            row,
            text=required_text,
            font=("Segoe UI", 10, "bold"),
            fg=required_fg,
            bg=base_bg,
            width=12,
            anchor="center"
        )
        required_label.pack(side="left", padx=(10, 0))

        action_frame = tk.Frame(row, bg=base_bg)
        action_frame.pack(side="right", padx=10)

        edit_btn = tk.Label(
            action_frame,
            text="Edit",
            font=("Segoe UI", 9, "bold"),
            fg="white",
            bg=EDIT_BG,
            padx=12,
            pady=5,
            cursor="hand2"
        )
        edit_btn.pack(side="left", padx=(0, 6))

        delete_btn = tk.Label(
            action_frame,
            text="Delete",
            font=("Segoe UI", 9, "bold"),
            fg="white",
            bg=DELETE_BG,
            padx=12,
            pady=5,
            cursor="hand2"
        )
        delete_btn.pack(side="left")

        row_data = {
            "frame": row,
            "no": no_label,
            "question": question_label,
            "required": required_label,
            "action_frame": action_frame,
            "edit": edit_btn,
            "delete": delete_btn,
            "base_bg": base_bg,
            "criterion_question_id": criterion_question_id
        }
        app.question_rows.append(row_data)

        def select_row(event, cqid=criterion_question_id):
            app.selected_question_link_id = cqid
            refresh_question_row_states(app)

        def hover_in(event, cqid=criterion_question_id):
            if app.selected_question_link_id != cqid:
                set_question_row_bg(app, cqid, ROW_HOVER)

        def hover_out(event, cqid=criterion_question_id, bg=base_bg):
            if app.selected_question_link_id != cqid:
                set_question_row_bg(app, cqid, bg)

        for widget in [row, no_label, question_label, required_label, action_frame]:
            widget.bind("<Button-1>", select_row)
            widget.bind("<Enter>", hover_in)
            widget.bind("<Leave>", hover_out)

        edit_btn.bind("<Enter>", lambda e, btn=edit_btn: btn.config(bg=EDIT_HOVER))
        edit_btn.bind("<Leave>", lambda e, btn=edit_btn: btn.config(bg=EDIT_BG))
        edit_btn.bind("<Button-1>", lambda e, cqid=criterion_question_id: open_edit_question_modal(app, cqid))

        delete_btn.bind("<Enter>", lambda e, btn=delete_btn: btn.config(bg=DELETE_HOVER))
        delete_btn.bind("<Leave>", lambda e, btn=delete_btn: btn.config(bg=DELETE_BG))
        delete_btn.bind("<Button-1>", lambda e, cqid=criterion_question_id: delete_question_link_by_id(app, cqid))

    refresh_question_row_states(app)
    app.question_list_frame.update_idletasks()
    app.question_canvas.configure(scrollregion=app.question_canvas.bbox("all"))


def set_question_row_bg(app, criterion_question_id, color):
    for row_data in app.question_rows:
        if row_data["criterion_question_id"] == criterion_question_id:
            row_data["frame"].config(bg=color)
            row_data["no"].config(bg=color)
            row_data["question"].config(bg=color)
            row_data["required"].config(bg=color)
            row_data["action_frame"].config(bg=color)
            break


def refresh_question_row_states(app):
    for row_data in app.question_rows:
        bg = ROW_SELECTED if row_data["criterion_question_id"] == app.selected_question_link_id else row_data["base_bg"]
        row_data["frame"].config(bg=bg)
        row_data["no"].config(bg=bg)
        row_data["question"].config(bg=bg)
        row_data["required"].config(bg=bg)
        row_data["action_frame"].config(bg=bg)


def open_add_question_modal(app):
    criterion_id = get_selected_criterion_id(app)
    if not criterion_id:
        messagebox.showwarning("No Criterion", "Please select a criterion first.")
        return

    open_question_modal(app, mode="add")


def open_edit_question_modal(app, criterion_question_id=None):
    if criterion_question_id is not None:
        app.selected_question_link_id = criterion_question_id

    if app.selected_question_link_id is None:
        messagebox.showwarning("No Selection", "Please select a question to edit.")
        return

    open_question_modal(app, mode="edit")


def get_selected_question_record(app):
    for item in app.question_data:
        if item["criterion_question_id"] == app.selected_question_link_id:
            return item
    return None


def open_question_modal(app, mode="add"):
    modal = tk.Toplevel(app.root)
    modal.title("Add Question" if mode == "add" else "Edit Question")
    modal.configure(bg="#f8f4f4")
    modal.resizable(False, False)
    modal.transient(app.root)
    modal.grab_set()

    width = 560
    height = 600

    screen_width = modal.winfo_screenwidth()
    screen_height = modal.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    modal.geometry(f"{width}x{height}+{x}+{y}")

    card = tk.Frame(
        modal,
        bg="white",
        highlightthickness=1,
        highlightbackground="#eadede"
    )
    card.pack(fill="both", expand=True, padx=18, pady=18)

    tk.Label(
        card,
        text="Add Question" if mode == "add" else "Edit Question",
        font=("Segoe UI", 15, "bold"),
        fg=TEXT_DARK,
        bg="white"
    ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(18, 15))

    tk.Label(
        card,
        text="Question Text",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="white"
    ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 6))

    question_text = tk.Text(
        card,
        font=("Segoe UI", 11),
        bg=ENTRY_BG,
        fg=TEXT_DARK,
        relief="solid",
        bd=1,
        height=7,
        wrap="word"
    )
    question_text.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 14))

    tk.Label(
        card,
        text="Required",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="white"
    ).grid(row=3, column=0, sticky="w", padx=20, pady=(0, 6))

    is_required_var = tk.IntVar(value=1)

    required_frame = tk.Frame(card, bg="white")
    required_frame.grid(row=4, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 18))

    required_yes = tk.Radiobutton(
        required_frame,
        text="Yes",
        variable=is_required_var,
        value=1,
        font=("Segoe UI", 10),
        bg="white",
        fg=TEXT_DARK,
        activebackground="white",
        activeforeground=TEXT_DARK,
        selectcolor="white"
    )
    required_yes.pack(side="left", padx=(0, 20))

    required_no = tk.Radiobutton(
        required_frame,
        text="No",
        variable=is_required_var,
        value=0,
        font=("Segoe UI", 10),
        bg="white",
        fg=TEXT_DARK,
        activebackground="white",
        activeforeground=TEXT_DARK,
        selectcolor="white"
    )
    required_no.pack(side="left")

    info_box = tk.Frame(card, bg="#f8eeee", highlightthickness=1, highlightbackground="#eadede")
    info_box.grid(row=5, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 16))

    tk.Label(
        info_box,
        text=f"Form: {app.question_form_var.get().strip() or '-'}",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="#f8eeee",
        anchor="w"
    ).pack(fill="x", padx=12, pady=(10, 4))

    tk.Label(
        info_box,
        text=f"Criterion: {app.question_criterion_var.get().strip() or '-'}",
        font=("Segoe UI", 10),
        fg=TEXT_MUTED,
        bg="#f8eeee",
        anchor="w"
    ).pack(fill="x", padx=12, pady=(0, 10))

    if mode == "edit":
        item = get_selected_question_record(app)
        if item:
            question_text.insert("1.0", item["question_text"])
            is_required_var.set(int(item["is_required"]))

    btn_frame = tk.Frame(card, bg="white")
    btn_frame.grid(row=6, column=0, columnspan=2, sticky="e", padx=20, pady=(0, 18))

    def save():
        criterion_id = get_selected_criterion_id(app)
        if not criterion_id:
            messagebox.showwarning("No Criterion", "Please select a criterion first.", parent=modal)
            return

        text_value = question_text.get("1.0", "end").strip()
        required_value = is_required_var.get()

        if not text_value:
            messagebox.showwarning("Missing Field", "Please enter the question text.", parent=modal)
            return

        try:
            if mode == "add":
                if question_text_exists_under_criterion(criterion_id, text_value):
                    messagebox.showwarning(
                        "Duplicate Question",
                        "This question already exists under the selected criterion.",
                        parent=modal
                    )
                    return

                insert_question_with_link(criterion_id, text_value, required_value)
                messagebox.showinfo("Success", "Question added successfully.", parent=modal)

            else:
                item = get_selected_question_record(app)
                if not item:
                    messagebox.showwarning("No Selection", "Please select a question to edit.", parent=modal)
                    return

                if question_text_exists_under_criterion(
                    criterion_id,
                    text_value,
                    exclude_question_id=item["question_id"]
                ):
                    messagebox.showwarning(
                        "Duplicate Question",
                        "This question already exists under the selected criterion.",
                        parent=modal
                    )
                    return

                update_question_and_link(
                    item["criterion_question_id"],
                    item["question_id"],
                    text_value,
                    required_value
                )
                messagebox.showinfo("Updated", "Question updated successfully.", parent=modal)

            modal.destroy()
            refresh_question_data(app)

        except Exception as e:
            messagebox.showerror("Database Error", str(e), parent=modal)

    cancel_btn = tk.Button(
        btn_frame,
        text="Cancel",
        font=("Segoe UI", 10, "bold"),
        bg="#ddd0d0",
        fg=TEXT_DARK,
        activebackground="#ccbaba",
        activeforeground=TEXT_DARK,
        relief="flat",
        bd=0,
        cursor="hand2",
        width=11,
        command=modal.destroy
    )
    cancel_btn.pack(side="left", padx=(0, 8), ipady=4)

    save_btn = tk.Button(
        btn_frame,
        text="Save",
        font=("Segoe UI", 10, "bold"),
        bg=ACCENT,
        fg="white",
        activebackground=ACCENT_HOVER,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        width=11,
        command=save
    )
    save_btn.pack(side="left", ipady=4)

    card.grid_columnconfigure(0, weight=1)
    card.grid_columnconfigure(1, weight=1)


def delete_question_link_by_id(app, criterion_question_id):
    app.selected_question_link_id = criterion_question_id
    delete_selected_question(app)


def delete_selected_question(app):
    if app.selected_question_link_id is None:
        messagebox.showwarning("No Selection", "Please select a question to delete.")
        return

    if question_is_used_in_answers(app.selected_question_link_id):
        messagebox.showwarning(
            "Cannot Delete",
            "This question cannot be deleted because it already has evaluation answers."
        )
        return

    confirm = messagebox.askyesno(
        "Delete Question",
        "Are you sure you want to delete the selected question from this criterion?"
    )

    if confirm:
        try:
            delete_criterion_question_link(app.selected_question_link_id)
            app.selected_question_link_id = None
            refresh_question_data(app)
            messagebox.showinfo("Deleted", "Question deleted successfully.")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))