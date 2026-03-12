import tkinter as tk
from tkinter import messagebox
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

STATUS_ACTIVE_BG = "#4f8a5b"
STATUS_INACTIVE_BG = "#9c7b7b"


# =========================
# DATABASE FUNCTIONS
# =========================
def fetch_evaluation_forms(search_text=""):
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    if search_text.strip():
        like = f"%{search_text.strip()}%"
        cursor.execute("""
            SELECT id, title, is_active, created_at, updated_at
            FROM evaluation_forms
            WHERE title LIKE %s
            ORDER BY id DESC
        """, (like,))
    else:
        cursor.execute("""
            SELECT id, title, is_active, created_at, updated_at
            FROM evaluation_forms
            ORDER BY id DESC
        """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def insert_evaluation_form(title, is_active):
    conn = get_connection()
    if not conn:
        raise Exception("Could not connect to database.")

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO evaluation_forms (title, is_active, created_at, updated_at)
        VALUES (%s, %s, NOW(), NOW())
    """, (title, is_active))
    conn.commit()
    cursor.close()
    conn.close()


def update_evaluation_form(form_id, title, is_active):
    conn = get_connection()
    if not conn:
        raise Exception("Could not connect to database.")

    cursor = conn.cursor()
    cursor.execute("""
        UPDATE evaluation_forms
        SET title = %s,
            is_active = %s,
            updated_at = NOW()
        WHERE id = %s
    """, (title, is_active, form_id))
    conn.commit()
    cursor.close()
    conn.close()


def form_has_dependencies(form_id):
    conn = get_connection()
    if not conn:
        return {"criteria": 0, "periods": 0}

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM criteria WHERE form_id = %s", (form_id,))
    criteria_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM evaluation_periods WHERE form_id = %s", (form_id,))
    period_count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return {
        "criteria": criteria_count,
        "periods": period_count
    }


def delete_evaluation_form(form_id):
    conn = get_connection()
    if not conn:
        raise Exception("Could not connect to database.")

    cursor = conn.cursor()
    cursor.execute("DELETE FROM evaluation_forms WHERE id = %s", (form_id,))
    conn.commit()
    cursor.close()
    conn.close()


# =========================
# PAGE
# =========================
def show_evaluation_form_page(app):
    app.clear_content()
    app.selected_form_id = None
    app.evaluation_form_rows = []
    app.evaluation_form_data = []

    if not hasattr(app, "evaluation_form_search_var"):
        app.evaluation_form_search_var = tk.StringVar()

    app.evaluation_form_search_var.set("")

    wrapper = tk.Frame(app.content_frame, bg=CONTENT_BG)
    wrapper.pack(fill="both", expand=True)

    # Header
    header_frame = tk.Frame(wrapper, bg=CONTENT_BG)
    header_frame.pack(fill="x", pady=(0, 15))

    left_header = tk.Frame(header_frame, bg=CONTENT_BG)
    left_header.pack(side="left")

    tk.Label(
        left_header,
        text="Evaluation Form Management",
        font=("Segoe UI", 18, "bold"),
        fg=TEXT_DARK,
        bg=CONTENT_BG
    ).pack(anchor="w")

    tk.Label(
        left_header,
        text="Create and manage evaluation forms before adding criteria and questions.",
        font=("Segoe UI", 10),
        fg=TEXT_MUTED,
        bg=CONTENT_BG
    ).pack(anchor="w", pady=(4, 0))

    right_header = tk.Frame(header_frame, bg=CONTENT_BG)
    right_header.pack(side="right")

    search_entry = tk.Entry(
        right_header,
        textvariable=app.evaluation_form_search_var,
        font=("Segoe UI", 10),
        bg=ENTRY_BG,
        fg=TEXT_DARK,
        relief="solid",
        bd=1,
        width=30
    )
    search_entry.pack(side="left", padx=(0, 10), ipady=5)

    add_btn = tk.Button(
        right_header,
        text="+ Add Form",
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
        command=lambda: open_evaluation_form_modal(app, mode="add")
    )
    add_btn.pack(side="left")

    # Card
    table_card = tk.Frame(
        wrapper,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=BORDER
    )
    table_card.pack(fill="both", expand=True)

    top_info = tk.Frame(table_card, bg=CARD_BG)
    top_info.pack(fill="x", padx=18, pady=(16, 10))

    app.evaluation_form_count_label = tk.Label(
        top_info,
        text="0 forms found",
        font=("Segoe UI", 10),
        fg=TEXT_MUTED,
        bg=CARD_BG
    )
    app.evaluation_form_count_label.pack(side="left")

    # Header row
    header_row = tk.Frame(table_card, bg="#f4ebeb", height=46)
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
        text="Form Title",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="#f4ebeb",
        width=34,
        anchor="w"
    ).pack(side="left", padx=(0, 10))

    tk.Label(
        header_row,
        text="Status",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="#f4ebeb",
        width=12,
        anchor="center"
    ).pack(side="left")

    tk.Label(
        header_row,
        text="Created",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="#f4ebeb",
        width=20,
        anchor="center"
    ).pack(side="left")

    tk.Label(
        header_row,
        text="Actions",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="#f4ebeb",
        width=22,
        anchor="center"
    ).pack(side="right", padx=(10, 10))

    # Scroll area
    list_container = tk.Frame(table_card, bg=CARD_BG)
    list_container.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    app.evaluation_form_canvas = tk.Canvas(
        list_container,
        bg=CARD_BG,
        highlightthickness=0
    )
    app.evaluation_form_canvas.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(
        list_container,
        orient="vertical",
        command=app.evaluation_form_canvas.yview
    )
    scrollbar.pack(side="right", fill="y")

    app.evaluation_form_canvas.configure(yscrollcommand=scrollbar.set)

    app.evaluation_form_list_frame = tk.Frame(app.evaluation_form_canvas, bg=CARD_BG)

    app.evaluation_form_canvas_window = app.evaluation_form_canvas.create_window(
        (0, 0),
        window=app.evaluation_form_list_frame,
        anchor="nw"
    )

    app.evaluation_form_list_frame.bind(
        "<Configure>",
        lambda e: app.evaluation_form_canvas.configure(
            scrollregion=app.evaluation_form_canvas.bbox("all")
        )
    )

    app.evaluation_form_canvas.bind(
        "<Configure>",
        lambda e: app.evaluation_form_canvas.itemconfig(
            app.evaluation_form_canvas_window,
            width=e.width
        )
    )

    app.evaluation_form_search_var.trace_add(
        "write",
        lambda *args: refresh_evaluation_form_data(app)
    )

    app.evaluation_form_canvas.bind("<Enter>", lambda e: _bind_mousewheel(app))
    app.evaluation_form_canvas.bind("<Leave>", lambda e: _unbind_mousewheel(app))

    refresh_evaluation_form_data(app)


def _bind_mousewheel(app):
    app.root.bind_all("<MouseWheel>", lambda event: _on_mousewheel(app, event))


def _unbind_mousewheel(app):
    app.root.unbind_all("<MouseWheel>")


def _on_mousewheel(app, event):
    if hasattr(app, "evaluation_form_canvas") and app.evaluation_form_canvas.winfo_exists():
        app.evaluation_form_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


def refresh_evaluation_form_data(app):
    search_text = app.evaluation_form_search_var.get().strip()
    app.evaluation_form_data = fetch_evaluation_forms(search_text)
    app.selected_form_id = None
    render_evaluation_form_rows(app)


def render_evaluation_form_rows(app):
    if not hasattr(app, "evaluation_form_list_frame") or not app.evaluation_form_list_frame.winfo_exists():
        return

    for widget in app.evaluation_form_list_frame.winfo_children():
        widget.destroy()

    app.evaluation_form_rows = []
    count = len(app.evaluation_form_data)

    if hasattr(app, "evaluation_form_count_label") and app.evaluation_form_count_label.winfo_exists():
        app.evaluation_form_count_label.config(text=f"{count} forms found")

    if not app.evaluation_form_data:
        empty_box = tk.Frame(app.evaluation_form_list_frame, bg=CARD_BG)
        empty_box.pack(fill="both", expand=True, pady=60)

        tk.Label(
            empty_box,
            text="No evaluation forms found",
            font=("Segoe UI", 15, "bold"),
            fg=TEXT_DARK,
            bg=CARD_BG
        ).pack(pady=(0, 8))

        tk.Label(
            empty_box,
            text="Add your first evaluation form to begin building criteria and questions.",
            font=("Segoe UI", 11),
            fg=TEXT_MUTED,
            bg=CARD_BG
        ).pack()

        app.evaluation_form_list_frame.update_idletasks()
        app.evaluation_form_canvas.configure(
            scrollregion=app.evaluation_form_canvas.bbox("all")
        )
        return

    for display_index, item in enumerate(app.evaluation_form_data):
        form_id = item["id"]
        base_bg = ROW_BG_1 if display_index % 2 == 0 else ROW_BG_2

        row = tk.Frame(
            app.evaluation_form_list_frame,
            bg=base_bg,
            height=58,
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

        title_label = tk.Label(
            row,
            text=item["title"],
            font=("Segoe UI", 10, "bold"),
            fg=TEXT_DARK,
            bg=base_bg,
            width=34,
            anchor="w"
        )
        title_label.pack(side="left", padx=(0, 10))

        status_text = "Active" if int(item["is_active"]) == 1 else "Inactive"
        status_fg = "#2e7d32" if int(item["is_active"]) == 1 else "#8d6e63"

        status_label = tk.Label(
            row,
            text=status_text,
            font=("Segoe UI", 10, "bold"),
            fg=status_fg,
            bg=base_bg,
            width=12,
            anchor="center"
        )
        status_label.pack(side="left")

        created_text = str(item["created_at"]) if item["created_at"] else "-"
        created_label = tk.Label(
            row,
            text=created_text,
            font=("Segoe UI", 10),
            fg=TEXT_MUTED,
            bg=base_bg,
            width=20,
            anchor="center"
        )
        created_label.pack(side="left")

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
            "title": title_label,
            "status": status_label,
            "created": created_label,
            "action_frame": action_frame,
            "edit": edit_btn,
            "delete": delete_btn,
            "base_bg": base_bg,
            "form_id": form_id
        }
        app.evaluation_form_rows.append(row_data)

        def select_row(event, fid=form_id):
            app.selected_form_id = fid
            refresh_form_row_states(app)

        def hover_in(event, fid=form_id):
            if app.selected_form_id != fid:
                set_form_row_bg(app, fid, ROW_HOVER)

        def hover_out(event, fid=form_id, bg=base_bg):
            if app.selected_form_id != fid:
                set_form_row_bg(app, fid, bg)

        for widget in [row, no_label, title_label, status_label, created_label, action_frame]:
            widget.bind("<Button-1>", select_row)
            widget.bind("<Enter>", hover_in)
            widget.bind("<Leave>", hover_out)

        edit_btn.bind("<Enter>", lambda e, btn=edit_btn: btn.config(bg=EDIT_HOVER))
        edit_btn.bind("<Leave>", lambda e, btn=edit_btn: btn.config(bg=EDIT_BG))
        edit_btn.bind("<Button-1>", lambda e, fid=form_id: open_evaluation_form_modal(app, mode="edit", form_id=fid))

        delete_btn.bind("<Enter>", lambda e, btn=delete_btn: btn.config(bg=DELETE_HOVER))
        delete_btn.bind("<Leave>", lambda e, btn=delete_btn: btn.config(bg=DELETE_BG))
        delete_btn.bind("<Button-1>", lambda e, fid=form_id: delete_evaluation_form_by_id(app, fid))

    refresh_form_row_states(app)
    app.evaluation_form_list_frame.update_idletasks()
    app.evaluation_form_canvas.configure(
        scrollregion=app.evaluation_form_canvas.bbox("all")
    )


def set_form_row_bg(app, form_id, color):
    for row_data in app.evaluation_form_rows:
        if row_data["form_id"] == form_id:
            row_data["frame"].config(bg=color)
            row_data["no"].config(bg=color)
            row_data["title"].config(bg=color)
            row_data["status_wrap"].config(bg=color)
            row_data["created"].config(bg=color)
            row_data["action_frame"].config(bg=color)
            break


def refresh_form_row_states(app):
    for row_data in app.evaluation_form_rows:
        bg = ROW_SELECTED if row_data["form_id"] == app.selected_form_id else row_data["base_bg"]
        row_data["frame"].config(bg=bg)
        row_data["no"].config(bg=bg)
        row_data["title"].config(bg=bg)
        row_data["status_wrap"].config(bg=bg)
        row_data["created"].config(bg=bg)
        row_data["action_frame"].config(bg=bg)


def get_selected_form_record(app, form_id=None):
    target_id = form_id if form_id is not None else app.selected_form_id
    for item in app.evaluation_form_data:
        if item["id"] == target_id:
            return item
    return None


def open_evaluation_form_modal(app, mode="add", form_id=None):
    if mode == "edit":
        if form_id is not None:
            app.selected_form_id = form_id

        if app.selected_form_id is None:
            messagebox.showwarning("No Selection", "Please select a form to edit.")
            return

    modal = tk.Toplevel(app.root)
    modal.title("Add Evaluation Form" if mode == "add" else "Edit Evaluation Form")
    modal.configure(bg="#f8f4f4")
    modal.resizable(False, False)
    modal.transient(app.root)
    modal.grab_set()

    width = 520
    height = 320

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
        text="Add Evaluation Form" if mode == "add" else "Edit Evaluation Form",
        font=("Segoe UI", 15, "bold"),
        fg=TEXT_DARK,
        bg="white"
    ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(18, 15))

    tk.Label(
        card,
        text="Form Title",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="white"
    ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 6))

    title_entry = tk.Entry(
        card,
        font=("Segoe UI", 11),
        bg=ENTRY_BG,
        fg=TEXT_DARK,
        relief="solid",
        bd=1
    )
    title_entry.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 12), ipady=7)

    tk.Label(
        card,
        text="Status",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="white"
    ).grid(row=3, column=0, sticky="w", padx=20, pady=(0, 6))

    is_active_var = tk.IntVar(value=1)

    status_frame = tk.Frame(card, bg="white")
    status_frame.grid(row=4, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 20))

    active_radio = tk.Radiobutton(
        status_frame,
        text="Active",
        variable=is_active_var,
        value=1,
        font=("Segoe UI", 10),
        bg="white",
        fg=TEXT_DARK,
        activebackground="white",
        activeforeground=TEXT_DARK,
        selectcolor="white"
    )
    active_radio.pack(side="left", padx=(0, 20))

    inactive_radio = tk.Radiobutton(
        status_frame,
        text="Inactive",
        variable=is_active_var,
        value=0,
        font=("Segoe UI", 10),
        bg="white",
        fg=TEXT_DARK,
        activebackground="white",
        activeforeground=TEXT_DARK,
        selectcolor="white"
    )
    inactive_radio.pack(side="left")

    if mode == "edit":
        record = get_selected_form_record(app)
        if record:
            title_entry.insert(0, record["title"])
            is_active_var.set(record["is_active"])

    btn_frame = tk.Frame(card, bg="white")
    btn_frame.grid(row=5, column=0, columnspan=2, sticky="e", padx=20, pady=(0, 18))

    def save():
        title = title_entry.get().strip()
        is_active = is_active_var.get()

        if not title:
            messagebox.showwarning("Missing Field", "Please enter a form title.", parent=modal)
            return

        try:
            if mode == "add":
                insert_evaluation_form(title, is_active)
                messagebox.showinfo("Success", "Evaluation form added successfully.", parent=modal)
            else:
                update_evaluation_form(app.selected_form_id, title, is_active)
                messagebox.showinfo("Updated", "Evaluation form updated successfully.", parent=modal)

            modal.destroy()
            refresh_evaluation_form_data(app)

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


def delete_evaluation_form_by_id(app, form_id):
    app.selected_form_id = form_id
    delete_selected_evaluation_form(app)


def delete_selected_evaluation_form(app):
    if app.selected_form_id is None:
        messagebox.showwarning("No Selection", "Please select a form to delete.")
        return

    dependencies = form_has_dependencies(app.selected_form_id)

    if dependencies["criteria"] > 0 or dependencies["periods"] > 0:
        messagebox.showwarning(
            "Cannot Delete",
            f"This form cannot be deleted because it is already being used.\n\n"
            f"Criteria linked: {dependencies['criteria']}\n"
            f"Evaluation schedules linked: {dependencies['periods']}"
        )
        return

    confirm = messagebox.askyesno(
        "Delete Evaluation Form",
        "Are you sure you want to delete the selected evaluation form?"
    )

    if confirm:
        try:
            delete_evaluation_form(app.selected_form_id)
            app.selected_form_id = None
            refresh_evaluation_form_data(app)
            messagebox.showinfo("Deleted", "Evaluation form deleted successfully.")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))