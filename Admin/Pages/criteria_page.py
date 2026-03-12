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


def fetch_criteria_by_form(form_id, search_text=""):
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    if search_text.strip():
        like = f"%{search_text.strip()}%"
        cursor.execute("""
            SELECT id, form_id, title, description, position
            FROM criteria
            WHERE form_id = %s
              AND (title LIKE %s OR description LIKE %s)
            ORDER BY position ASC, id ASC
        """, (form_id, like, like))
    else:
        cursor.execute("""
            SELECT id, form_id, title, description, position
            FROM criteria
            WHERE form_id = %s
            ORDER BY position ASC, id ASC
        """, (form_id,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_next_criteria_position(form_id):
    conn = get_connection()
    if not conn:
        return 1

    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(MAX(position), 0) + 1
        FROM criteria
        WHERE form_id = %s
    """, (form_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else 1


def insert_criterion(form_id, title, description):
    conn = get_connection()
    if not conn:
        raise Exception("Could not connect to database.")

    cursor = conn.cursor()
    next_position = get_next_criteria_position(form_id)

    cursor.execute("""
        INSERT INTO criteria (form_id, title, description, position, created_at, updated_at)
        VALUES (%s, %s, %s, %s, NOW(), NOW())
    """, (form_id, title, description, next_position))

    conn.commit()
    cursor.close()
    conn.close()


def update_criterion(criteria_id, title, description):
    conn = get_connection()
    if not conn:
        raise Exception("Could not connect to database.")

    cursor = conn.cursor()
    cursor.execute("""
        UPDATE criteria
        SET title = %s,
            description = %s,
            updated_at = NOW()
        WHERE id = %s
    """, (title, description, criteria_id))

    conn.commit()
    cursor.close()
    conn.close()


def criterion_has_questions(criteria_id):
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM criterion_questions
        WHERE criterion_id = %s
    """, (criteria_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] > 0 if row else False


def delete_criterion(criteria_id):
    conn = get_connection()
    if not conn:
        raise Exception("Could not connect to database.")

    cursor = conn.cursor()
    cursor.execute("DELETE FROM criteria WHERE id = %s", (criteria_id,))
    conn.commit()
    cursor.close()
    conn.close()


# =========================
# PAGE
# =========================
def show_criteria_page(app):
    app.clear_content()
    app.selected_criteria_id = None
    app.criteria_rows = []
    app.criteria_data = []
    app.criteria_form_map = {}

    if not hasattr(app, "criteria_search_var"):
        app.criteria_search_var = tk.StringVar()

    if not hasattr(app, "criteria_form_var"):
        app.criteria_form_var = tk.StringVar()

    app.criteria_search_var.set("")

    wrapper = tk.Frame(app.content_frame, bg=CONTENT_BG)
    wrapper.pack(fill="both", expand=True)

    # Header
    header_frame = tk.Frame(wrapper, bg=CONTENT_BG)
    header_frame.pack(fill="x", pady=(0, 15))

    left_header = tk.Frame(header_frame, bg=CONTENT_BG)
    left_header.pack(side="left")

    tk.Label(
        left_header,
        text="Criteria Management",
        font=("Segoe UI", 18, "bold"),
        fg=TEXT_DARK,
        bg=CONTENT_BG
    ).pack(anchor="w")

    tk.Label(
        left_header,
        text="Manage criteria based on the selected evaluation form.",
        font=("Segoe UI", 10),
        fg=TEXT_MUTED,
        bg=CONTENT_BG
    ).pack(anchor="w", pady=(4, 0))

    right_header = tk.Frame(header_frame, bg=CONTENT_BG)
    right_header.pack(side="right")

    # Form combobox
    app.criteria_form_combo = ttk.Combobox(
        right_header,
        textvariable=app.criteria_form_var,
        state="readonly",
        width=28
    )
    app.criteria_form_combo.pack(side="left", padx=(0, 10), ipady=4)
    app.criteria_form_combo.bind("<<ComboboxSelected>>", lambda e: refresh_criteria_data(app))

    # Search
    search_entry = tk.Entry(
        right_header,
        textvariable=app.criteria_search_var,
        font=("Segoe UI", 10),
        bg=ENTRY_BG,
        fg=TEXT_DARK,
        relief="solid",
        bd=1,
        width=28
    )
    search_entry.pack(side="left", padx=(0, 10), ipady=5)

    add_btn = tk.Button(
        right_header,
        text="+ Add Criteria",
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
        command=lambda: open_add_criteria_modal(app)
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

    app.criteria_count_label = tk.Label(
        top_info,
        text="0 criteria found",
        font=("Segoe UI", 10),
        fg=TEXT_MUTED,
        bg=CARD_BG
    )
    app.criteria_count_label.pack(side="left")

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
        text="Criteria Name",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="#f4ebeb",
        width=24,
        anchor="w"
    ).pack(side="left", padx=(0, 10))

    tk.Label(
        header_row,
        text="Description",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="#f4ebeb",
        anchor="w"
    ).pack(side="left", fill="x", expand=True)

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

    app.criteria_canvas = tk.Canvas(list_container, bg=CARD_BG, highlightthickness=0)
    app.criteria_canvas.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(list_container, orient="vertical", command=app.criteria_canvas.yview)
    scrollbar.pack(side="right", fill="y")

    app.criteria_canvas.configure(yscrollcommand=scrollbar.set)

    app.criteria_list_frame = tk.Frame(app.criteria_canvas, bg=CARD_BG)

    app.criteria_canvas_window = app.criteria_canvas.create_window(
        (0, 0),
        window=app.criteria_list_frame,
        anchor="nw"
    )

    app.criteria_list_frame.bind(
        "<Configure>",
        lambda e: app.criteria_canvas.configure(scrollregion=app.criteria_canvas.bbox("all"))
    )

    app.criteria_canvas.bind(
        "<Configure>",
        lambda e: app.criteria_canvas.itemconfig(app.criteria_canvas_window, width=e.width)
    )

    app.criteria_search_var.trace_add("write", lambda *args: _on_criteria_search_change(app))

    app.criteria_canvas.bind("<Enter>", lambda e: _bind_mousewheel(app))
    app.criteria_canvas.bind("<Leave>", lambda e: _unbind_mousewheel(app))

    load_criteria_forms(app)
    refresh_criteria_data(app)


def _bind_mousewheel(app):
    app.root.bind_all("<MouseWheel>", lambda event: _on_mousewheel(app, event))


def _unbind_mousewheel(app):
    app.root.unbind_all("<MouseWheel>")


def _on_criteria_search_change(app):
    if hasattr(app, "criteria_list_frame") and app.criteria_list_frame.winfo_exists():
        refresh_criteria_data(app)


def _on_mousewheel(app, event):
    if hasattr(app, "criteria_canvas") and app.criteria_canvas.winfo_exists():
        app.criteria_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


def load_criteria_forms(app):
    forms = fetch_evaluation_forms()
    app.criteria_form_map = {form["title"]: form["id"] for form in forms}

    titles = list(app.criteria_form_map.keys())
    app.criteria_form_combo["values"] = titles

    if titles:
        app.criteria_form_var.set(titles[0])
    else:
        app.criteria_form_var.set("")


def get_selected_form_id(app):
    selected_title = app.criteria_form_var.get().strip()
    return app.criteria_form_map.get(selected_title)


def refresh_criteria_data(app):
    form_id = get_selected_form_id(app)

    if not form_id:
        app.criteria_data = []
        app.selected_criteria_id = None
        render_criteria_rows(app)
        return

    search_text = app.criteria_search_var.get().strip()
    app.criteria_data = fetch_criteria_by_form(form_id, search_text)
    app.selected_criteria_id = None
    render_criteria_rows(app)


def render_criteria_rows(app):
    if not hasattr(app, "criteria_list_frame") or not app.criteria_list_frame.winfo_exists():
        return

    for widget in app.criteria_list_frame.winfo_children():
        widget.destroy()

    app.criteria_rows = []
    count = len(app.criteria_data)

    if hasattr(app, "criteria_count_label") and app.criteria_count_label.winfo_exists():
        app.criteria_count_label.config(text=f"{count} criteria found")

    if not app.criteria_form_var.get().strip():
        empty_box = tk.Frame(app.criteria_list_frame, bg=CARD_BG)
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

        app.criteria_list_frame.update_idletasks()
        app.criteria_canvas.configure(scrollregion=app.criteria_canvas.bbox("all"))
        return

    if not app.criteria_data:
        empty_box = tk.Frame(app.criteria_list_frame, bg=CARD_BG)
        empty_box.pack(fill="both", expand=True, pady=50)

        tk.Label(
            empty_box,
            text="No criteria found",
            font=("Segoe UI", 15, "bold"),
            fg=TEXT_DARK,
            bg=CARD_BG
        ).pack(pady=(0, 8))

        tk.Label(
            empty_box,
            text="Try a different search or add a new criterion.",
            font=("Segoe UI", 11),
            fg=TEXT_MUTED,
            bg=CARD_BG
        ).pack()

        app.criteria_list_frame.update_idletasks()
        app.criteria_canvas.configure(scrollregion=app.criteria_canvas.bbox("all"))
        return

    for display_index, item in enumerate(app.criteria_data):
        criteria_id = item["id"]
        base_bg = ROW_BG_1 if display_index % 2 == 0 else ROW_BG_2

        row = tk.Frame(
            app.criteria_list_frame,
            bg=base_bg,
            height=56,
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

        name_label = tk.Label(
            row,
            text=item["title"],
            font=("Segoe UI", 10, "bold"),
            fg=TEXT_DARK,
            bg=base_bg,
            width=24,
            anchor="w"
        )
        name_label.pack(side="left", padx=(0, 10))

        desc_label = tk.Label(
            row,
            text=item["description"] if item["description"] else "No description provided.",
            font=("Segoe UI", 10),
            fg=TEXT_MUTED,
            bg=base_bg,
            anchor="w",
            justify="left",
            wraplength=580
        )
        desc_label.pack(side="left", fill="x", expand=True)

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
            "name": name_label,
            "desc": desc_label,
            "action_frame": action_frame,
            "edit": edit_btn,
            "delete": delete_btn,
            "base_bg": base_bg,
            "criteria_id": criteria_id
        }
        app.criteria_rows.append(row_data)

        def select_row(event, cid=criteria_id):
            app.selected_criteria_id = cid
            refresh_row_states(app)

        def hover_in(event, cid=criteria_id):
            if app.selected_criteria_id != cid:
                set_row_bg_by_criteria_id(app, cid, ROW_HOVER)

        def hover_out(event, cid=criteria_id, bg=base_bg):
            if app.selected_criteria_id != cid:
                set_row_bg_by_criteria_id(app, cid, bg)

        for widget in [row, no_label, name_label, desc_label, action_frame]:
            widget.bind("<Button-1>", select_row)
            widget.bind("<Enter>", hover_in)
            widget.bind("<Leave>", hover_out)

        edit_btn.bind("<Enter>", lambda e, btn=edit_btn: btn.config(bg=EDIT_HOVER))
        edit_btn.bind("<Leave>", lambda e, btn=edit_btn: btn.config(bg=EDIT_BG))
        edit_btn.bind("<Button-1>", lambda e, cid=criteria_id: open_edit_criteria_modal(app, cid))

        delete_btn.bind("<Enter>", lambda e, btn=delete_btn: btn.config(bg=DELETE_HOVER))
        delete_btn.bind("<Leave>", lambda e, btn=delete_btn: btn.config(bg=DELETE_BG))
        delete_btn.bind("<Button-1>", lambda e, cid=criteria_id: delete_criteria_by_id(app, cid))

    refresh_row_states(app)
    app.criteria_list_frame.update_idletasks()
    app.criteria_canvas.configure(scrollregion=app.criteria_canvas.bbox("all"))


def set_row_bg_by_criteria_id(app, criteria_id, color):
    for row_data in app.criteria_rows:
        if row_data["criteria_id"] == criteria_id:
            row_data["frame"].config(bg=color)
            row_data["no"].config(bg=color)
            row_data["name"].config(bg=color)
            row_data["desc"].config(bg=color)
            row_data["action_frame"].config(bg=color)
            break


def refresh_row_states(app):
    for row_data in app.criteria_rows:
        bg = ROW_SELECTED if row_data["criteria_id"] == app.selected_criteria_id else row_data["base_bg"]
        row_data["frame"].config(bg=bg)
        row_data["no"].config(bg=bg)
        row_data["name"].config(bg=bg)
        row_data["desc"].config(bg=bg)
        row_data["action_frame"].config(bg=bg)


def open_add_criteria_modal(app):
    form_id = get_selected_form_id(app)
    if not form_id:
        messagebox.showwarning("No Form", "Please create/select an evaluation form first.")
        return

    open_criteria_modal(app, mode="add")


def open_edit_criteria_modal(app, criteria_id=None):
    if criteria_id is not None:
        app.selected_criteria_id = criteria_id

    if app.selected_criteria_id is None:
        messagebox.showwarning("No Selection", "Please select a criterion to edit.")
        return

    open_criteria_modal(app, mode="edit")


def get_selected_criteria_record(app):
    for item in app.criteria_data:
        if item["id"] == app.selected_criteria_id:
            return item
    return None


def open_criteria_modal(app, mode="add"):
    modal = tk.Toplevel(app.root)
    modal.title("Add Criteria" if mode == "add" else "Edit Criteria")
    modal.configure(bg="#f8f4f4")
    modal.resizable(False, False)
    modal.transient(app.root)
    modal.grab_set()

    width = 500
    height = 400

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
        text="Add Criteria" if mode == "add" else "Edit Criteria",
        font=("Segoe UI", 15, "bold"),
        fg=TEXT_DARK,
        bg="white"
    ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(18, 15))

    tk.Label(
        card,
        text="Criteria Name",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="white"
    ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 6))

    name_entry = tk.Entry(
        card,
        font=("Segoe UI", 11),
        bg=ENTRY_BG,
        fg=TEXT_DARK,
        relief="solid",
        bd=1
    )
    name_entry.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 12), ipady=6)

    tk.Label(
        card,
        text="Description",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="white"
    ).grid(row=3, column=0, sticky="w", padx=20, pady=(0, 6))

    description_text = tk.Text(
        card,
        font=("Segoe UI", 11),
        bg=ENTRY_BG,
        fg=TEXT_DARK,
        relief="solid",
        bd=1,
        height=5
    )
    description_text.grid(row=4, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 16))

    if mode == "edit":
        item = get_selected_criteria_record(app)
        if item:
            name_entry.insert(0, item["title"])
            description_text.insert("1.0", item["description"] if item["description"] else "")

    btn_frame = tk.Frame(card, bg="white")
    btn_frame.grid(row=5, column=0, columnspan=2, sticky="e", padx=20, pady=(0, 18))

    def save():
        title = name_entry.get().strip()
        description = description_text.get("1.0", "end").strip()

        if not title:
            messagebox.showwarning("Missing Field", "Please enter a criteria name.", parent=modal)
            return

        description_value = description if description else "No description provided."

        try:
            if mode == "add":
                form_id = get_selected_form_id(app)
                if not form_id:
                    messagebox.showwarning("No Form", "Please select an evaluation form first.", parent=modal)
                    return

                insert_criterion(form_id, title, description_value)
                messagebox.showinfo("Success", "Criteria added successfully.", parent=modal)

            else:
                if app.selected_criteria_id is None:
                    messagebox.showwarning("No Selection", "Please select a criterion to edit.", parent=modal)
                    return

                update_criterion(app.selected_criteria_id, title, description_value)
                messagebox.showinfo("Updated", "Criteria updated successfully.", parent=modal)

            modal.destroy()
            refresh_criteria_data(app)

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


def delete_criteria_by_id(app, criteria_id):
    app.selected_criteria_id = criteria_id
    delete_selected_criteria(app)


def delete_selected_criteria(app):
    if app.selected_criteria_id is None:
        messagebox.showwarning("No Selection", "Please select a criterion to delete.")
        return

    if criterion_has_questions(app.selected_criteria_id):
        messagebox.showwarning(
            "Cannot Delete",
            "This criterion cannot be deleted because it is already linked to one or more questions."
        )
        return

    confirm = messagebox.askyesno(
        "Delete Criteria",
        "Are you sure you want to delete the selected criterion?"
    )

    if confirm:
        try:
            delete_criterion(app.selected_criteria_id)
            app.selected_criteria_id = None
            refresh_criteria_data(app)
            messagebox.showinfo("Deleted", "Criteria deleted successfully.")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))