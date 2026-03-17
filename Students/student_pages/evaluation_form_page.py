import tkinter as tk
from tkinter import messagebox
from db_connection import get_connection

PAGE_BG = "#fffafa"
CARD_BG = "#ffffff"
TEXT_DARK = "#4a2c2c"
TEXT_MUTED = "#7a5c5c"
BORDER = "#eadede"

ACCENT = "#8b4a4a"
ACCENT_HOVER = "#723939"

NEUTRAL = "#a98f8f"
NEUTRAL_HOVER = "#927777"

LIGHT_ACCENT = "#f7efef"
LIGHT_BORDER = "#f1e4e4"
ROW_ALT = "#fcf7f7"
MISSING_BG = "#fff2f2"


def get_open_evaluation_period_for_class_offering(class_offering_id):
    conn = get_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                ep.id AS evaluation_period_id,
                ep.form_id,
                ep.term_id,
                ep.status,
                ep.starts_at,
                ep.ends_at
            FROM class_offerings co
            INNER JOIN evaluation_periods ep
                ON ep.term_id = co.term_id
            WHERE co.id = %s
              AND ep.status = 'open'
            ORDER BY ep.starts_at DESC, ep.id DESC
            LIMIT 1
        """
        cursor.execute(query, (class_offering_id,))
        return cursor.fetchone()
    except Exception as e:
        print("get_open_evaluation_period_for_class_offering error:", e)
        return None
    finally:
        conn.close()


def create_or_get_evaluation(student_id, class_offering_id):
    period = get_open_evaluation_period_for_class_offering(class_offering_id)
    if not period:
        return None

    conn = get_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, status, evaluation_period_id
            FROM evaluations
            WHERE student_id = %s
              AND class_offering_id = %s
              AND evaluation_period_id = %s
            LIMIT 1
        """, (
            student_id,
            class_offering_id,
            period["evaluation_period_id"]
        ))
        existing = cursor.fetchone()

        if existing:
            return {
                "evaluation_id": existing["id"],
                "status": existing["status"],
                "evaluation_period_id": existing["evaluation_period_id"],
                "form_id": period["form_id"],
                "starts_at": period["starts_at"],
                "ends_at": period["ends_at"],
                "period_status": period["status"],
            }

        cursor.execute("""
            INSERT INTO evaluations (
                evaluation_period_id,
                class_offering_id,
                student_id,
                status,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, 'draft', NOW(), NOW())
        """, (
            period["evaluation_period_id"],
            class_offering_id,
            student_id
        ))
        conn.commit()

        return {
            "evaluation_id": cursor.lastrowid,
            "status": "draft",
            "evaluation_period_id": period["evaluation_period_id"],
            "form_id": period["form_id"],
            "starts_at": period["starts_at"],
            "ends_at": period["ends_at"],
            "period_status": period["status"],
        }

    except Exception as e:
        print("create_or_get_evaluation error:", e)
        return None
    finally:
        conn.close()


def get_evaluation_questions(evaluation_id):
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                c.id AS criterion_id,
                c.title AS criterion_title,
                c.description AS criterion_description,
                cq.id AS criterion_question_id,
                cq.position AS question_position,
                cq.is_required,
                q.question_text
            FROM evaluations e
            INNER JOIN evaluation_periods ep
                ON ep.id = e.evaluation_period_id
            INNER JOIN criteria c
                ON c.form_id = ep.form_id
            INNER JOIN criterion_questions cq
                ON cq.criterion_id = c.id
            INNER JOIN questions q
                ON q.id = cq.question_id
            WHERE e.id = %s
            ORDER BY c.position ASC, cq.position ASC
        """, (evaluation_id,))
        return cursor.fetchall()
    except Exception as e:
        print("get_evaluation_questions error:", e)
        return []
    finally:
        conn.close()


def get_existing_answers(evaluation_id):
    conn = get_connection()
    if conn is None:
        return {}

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT criterion_question_id, rating_value
            FROM evaluation_answers
            WHERE evaluation_id = %s
        """, (evaluation_id,))
        rows = cursor.fetchall()
        return {row["criterion_question_id"]: row["rating_value"] for row in rows}
    except Exception as e:
        print("get_existing_answers error:", e)
        return {}
    finally:
        conn.close()


def get_existing_comment(evaluation_id):
    conn = get_connection()
    if conn is None:
        return ""

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT comment_text
            FROM evaluation_comments
            WHERE evaluation_id = %s
            ORDER BY id DESC
            LIMIT 1
        """, (evaluation_id,))
        row = cursor.fetchone()
        return row["comment_text"] if row else ""
    except Exception as e:
        print("get_existing_comment error:", e)
        return ""
    finally:
        conn.close()


def save_evaluation_answers(evaluation_id, answers, comment_text):
    conn = get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM evaluation_answers WHERE evaluation_id = %s",
            (evaluation_id,)
        )

        for criterion_question_id, rating_value in answers.items():
            cursor.execute("""
                INSERT INTO evaluation_answers (
                    evaluation_id,
                    criterion_question_id,
                    rating_value,
                    created_at,
                    updated_at
                )
                VALUES (%s, %s, %s, NOW(), NOW())
            """, (evaluation_id, criterion_question_id, rating_value))

        cursor.execute(
            "DELETE FROM evaluation_comments WHERE evaluation_id = %s",
            (evaluation_id,)
        )

        comment_text = (comment_text or "").strip()
        if comment_text:
            cursor.execute("""
                INSERT INTO evaluation_comments (
                    evaluation_id,
                    comment_text,
                    created_at,
                    updated_at
                )
                VALUES (%s, %s, NOW(), NOW())
            """, (evaluation_id, comment_text))

        cursor.execute(
            "UPDATE evaluations SET updated_at = NOW() WHERE id = %s",
            (evaluation_id,)
        )

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        print("save_evaluation_answers error:", e)
        return False
    finally:
        conn.close()


def submit_evaluation(evaluation_id):
    conn = get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE evaluations
            SET status = 'submitted',
                submitted_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
        """, (evaluation_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print("submit_evaluation error:", e)
        return False
    finally:
        conn.close()

# def submit_evaluation(evaluation_id):
#     conn = get_connection()
#     if conn is None:
#         return False
#
#     try:
#         cursor = conn.cursor()
#         cursor.execute("""
#             UPDATE evaluations
#             SET status = 'submitted',
#                 submitted_at = NOW(),
#                 updated_at = NOW()
#             WHERE id = %s
#         """, (evaluation_id,))
#         conn.commit()
#         return True
#     except Exception as e:
#         conn.rollback()
#         print("submit_evaluation error:", e)
#         return False
#     finally:
#         conn.close()


# =========================
# UI HELPERS
# =========================

def _clear_content(app):
    for widget in app.content_frame.winfo_children():
        widget.destroy()


def _build_scrollable_area(parent, bg):
    outer = tk.Frame(parent, bg=bg)
    outer.pack(fill="both", expand=True)

    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0, bd=0)
    scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=bg)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def resize_inner(event):
        canvas.itemconfig(window_id, width=event.width)

    canvas.bind("<Configure>", resize_inner)
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_mousewheel(event):
        try:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    return scrollable_frame, canvas


def styled_button(parent, text, bg, hover, command):
    btn = tk.Button(
        parent,
        text=text,
        font=("Segoe UI", 10, "bold"),
        bg=bg,
        fg="white",
        activebackground=hover,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=18,
        pady=10,
        command=command
    )
    btn.bind("<Enter>", lambda e: e.widget.config(bg=hover))
    btn.bind("<Leave>", lambda e: e.widget.config(bg=bg))
    return btn


def rating_label(value):
    return {
        1: "Poor",
        2: "Fair",
        3: "Good",
        4: "Very Good",
        5: "Excellent"
    }.get(value, "")


def create_rating_header(parent):
    header = tk.Frame(parent, bg=LIGHT_ACCENT, highlightthickness=1, highlightbackground=LIGHT_BORDER)
    header.pack(fill="x", padx=20, pady=(0, 8))

    tk.Label(
        header,
        text="Question",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg=LIGHT_ACCENT,
        anchor="w"
    ).grid(row=0, column=0, sticky="w", padx=(14, 8), pady=10)

    for i in range(1, 6):
        tk.Label(
            header,
            text=f"{i}\n{rating_label(i)}",
            font=("Segoe UI", 8, "bold"),
            fg=TEXT_DARK,
            bg=LIGHT_ACCENT,
            justify="center"
        ).grid(row=0, column=i, padx=4, pady=8, sticky="nsew")

    header.grid_columnconfigure(0, weight=1)
    for i in range(1, 6):
        header.grid_columnconfigure(i, weight=0, minsize=78)

    return header


def update_progress(progress_label, answers_vars):
    total = len(answers_vars)
    answered = sum(1 for var in answers_vars.values() if var.get() > 0)
    progress_label.config(text=f"Answered {answered} of {total} questions")


# =========================
# MAIN PAGE
# =========================

def show_evaluation_form(app, subject_item, preview=False):
    _clear_content(app)

    evaluation_data = create_or_get_evaluation(
        app.student_id,
        subject_item["class_offering_id"]
    )

    if not evaluation_data:
        messagebox.showwarning(
            "Evaluation Unavailable",
            "There is no open evaluation period for this subject."
        )
        app.show_my_evaluations()
        return

    evaluation_id = evaluation_data["evaluation_id"]
    questions = get_evaluation_questions(evaluation_id)

    if not questions:
        messagebox.showwarning(
            "No Questionnaire",
            "No criteria/questions were found for the active evaluation form."
        )
        app.show_my_evaluations()
        return

    existing_answers = get_existing_answers(evaluation_id)
    existing_comment = get_existing_comment(evaluation_id)

    container = tk.Frame(app.content_frame, bg=PAGE_BG)
    container.pack(fill="both", expand=True)

    # Header card
    header_card = tk.Frame(
        container,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=BORDER
    )
    header_card.pack(fill="x", padx=6, pady=(0, 10))

    title_text = "Preview Evaluation" if preview else "Evaluation Form"

    tk.Label(
        header_card,
        text=title_text,
        font=("Segoe UI", 19, "bold"),
        fg=TEXT_DARK,
        bg=CARD_BG
    ).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 4), columnspan=2)

    tk.Label(
        header_card,
        text=f"{subject_item['subject_code']} - {subject_item['descriptive_title']}",
        font=("Segoe UI", 12, "bold"),
        fg=ACCENT,
        bg=CARD_BG
    ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 6), columnspan=2)

    tk.Label(
        header_card,
        text=f"Faculty: {subject_item['faculty_name']}",
        font=("Segoe UI", 10),
        fg=TEXT_MUTED,
        bg=CARD_BG
    ).grid(row=2, column=0, sticky="w", padx=20, pady=(0, 4))

    period_text = f"Period: {evaluation_data['starts_at']} to {evaluation_data['ends_at']}"

    tk.Label(
        header_card,
        text=period_text,
        font=("Segoe UI", 10),
        fg=TEXT_MUTED,
        bg=CARD_BG
    ).grid(row=2, column=1, sticky="e", padx=20, pady=(0, 4))

    status_text = "Submitted" if preview else "Draft / Ongoing"
    status_bg = "#edf7ef" if preview else LIGHT_ACCENT
    status_fg = "#3f6b4b" if preview else ACCENT

    tk.Label(
        header_card,
        text=status_text,
        font=("Segoe UI", 9, "bold"),
        fg=status_fg,
        bg=status_bg,
        padx=12,
        pady=5
    ).grid(row=3, column=0, sticky="w", padx=20, pady=(6, 16))

    progress_label = tk.Label(
        header_card,
        text="",
        font=("Segoe UI", 9),
        fg=TEXT_MUTED,
        bg=CARD_BG
    )
    progress_label.grid(row=3, column=1, sticky="e", padx=20, pady=(6, 16))

    header_card.grid_columnconfigure(0, weight=1)
    header_card.grid_columnconfigure(1, weight=1)

    # Scrollable content
    scroll_area, canvas = _build_scrollable_area(container, PAGE_BG)

    answers_vars = {}
    row_frames = {}
    question_rows = []
    current_criterion_id = None
    criterion_card = None
    question_no = 0

    for q in questions:
        if current_criterion_id != q["criterion_id"]:
            current_criterion_id = q["criterion_id"]

            criterion_card = tk.Frame(
                scroll_area,
                bg=CARD_BG,
                highlightthickness=1,
                highlightbackground=BORDER
            )
            criterion_card.pack(fill="x", padx=6, pady=8)

            tk.Label(
                criterion_card,
                text=q["criterion_title"],
                font=("Segoe UI", 13, "bold"),
                fg=TEXT_DARK,
                bg=CARD_BG
            ).pack(anchor="w", padx=20, pady=(16, 4))

            if q["criterion_description"]:
                tk.Label(
                    criterion_card,
                    text=q["criterion_description"],
                    font=("Segoe UI", 9),
                    fg=TEXT_MUTED,
                    bg=CARD_BG,
                    wraplength=1150,
                    justify="left"
                ).pack(anchor="w", padx=20, pady=(0, 10))

            create_rating_header(criterion_card)

        question_no += 1
        row_bg = CARD_BG if question_no % 2 == 1 else ROW_ALT

        row_frame = tk.Frame(
            criterion_card,
            bg=row_bg,
            highlightthickness=1,
            highlightbackground=LIGHT_BORDER
        )
        row_frame.pack(fill="x", padx=20, pady=(0, 6))

        question_rows.append((q["criterion_question_id"], row_frame))
        row_frames[q["criterion_question_id"]] = row_frame

        question_text = tk.Label(
            row_frame,
            text=f"{question_no}. {q['question_text']}",
            font=("Segoe UI", 10),
            fg=TEXT_DARK,
            bg=row_bg,
            anchor="w",
            justify="left",
            wraplength=760
        )
        question_text.grid(row=0, column=0, sticky="nsew", padx=(14, 8), pady=12)

        var = tk.IntVar(value=existing_answers.get(q["criterion_question_id"], 0))
        answers_vars[q["criterion_question_id"]] = var

        def on_change(*_args):
            update_progress(progress_label, answers_vars)

        var.trace_add("write", on_change)

        for i in range(1, 6):
            cell = tk.Frame(row_frame, bg=row_bg)
            cell.grid(row=0, column=i, padx=4, pady=8, sticky="nsew")

            rb = tk.Radiobutton(
                cell,
                variable=var,
                value=i,
                bg=row_bg,
                activebackground=row_bg,
                state="disabled" if preview else "normal",
                cursor="hand2" if not preview else "arrow"
            )
            rb.pack(anchor="center")

        row_frame.grid_columnconfigure(0, weight=1)
        for i in range(1, 6):
            row_frame.grid_columnconfigure(i, weight=0, minsize=78)

    # Comment card
    comment_card = tk.Frame(
        scroll_area,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=BORDER
    )
    comment_card.pack(fill="x", padx=6, pady=8)

    tk.Label(
        comment_card,
        text="Additional Comment",
        font=("Segoe UI", 13, "bold"),
        fg=TEXT_DARK,
        bg=CARD_BG
    ).pack(anchor="w", padx=20, pady=(16, 6))

    tk.Label(
        comment_card,
        text="Share your remarks, suggestions, or feedback about the instructor.",
        font=("Segoe UI", 9),
        fg=TEXT_MUTED,
        bg=CARD_BG
    ).pack(anchor="w", padx=20, pady=(0, 8))

    comment_text = tk.Text(
        comment_card,
        height=6,
        font=("Segoe UI", 10),
        bg="#fffdfd",
        fg=TEXT_DARK,
        relief="flat",
        highlightthickness=1,
        highlightbackground=LIGHT_BORDER,
        wrap="word",
        padx=10,
        pady=10
    )
    comment_text.pack(fill="x", padx=20, pady=(0, 18))
    comment_text.insert("1.0", existing_comment)

    if preview:
        comment_text.config(state="disabled")

    update_progress(progress_label, answers_vars)

    # Action bar
    action_bar = tk.Frame(
        container,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=BORDER
    )
    action_bar.pack(fill="x", padx=6, pady=(10, 0))

    left_actions = tk.Frame(action_bar, bg=CARD_BG)
    left_actions.pack(side="left", padx=16, pady=14)

    right_actions = tk.Frame(action_bar, bg=CARD_BG)
    right_actions.pack(side="right", padx=16, pady=14)

    tk.Label(
        left_actions,
        text="Choose one rating per question. Review your answers before submitting.",
        font=("Segoe UI", 9),
        fg=TEXT_MUTED,
        bg=CARD_BG
    ).pack(anchor="w")

    def reset_row_highlights():
        for idx, (cq_id, frame) in enumerate(question_rows, start=1):
            base = CARD_BG if idx % 2 == 1 else ROW_ALT
            frame.config(bg=base)
            for child in frame.winfo_children():
                try:
                    child.config(bg=base, activebackground=base)
                except Exception:
                    pass
                for inner in child.winfo_children():
                    try:
                        inner.config(bg=base, activebackground=base)
                    except Exception:
                        pass

    def highlight_missing_rows(missing_ids):
        reset_row_highlights()
        first_frame = None

        for cq_id in missing_ids:
            frame = row_frames.get(cq_id)
            if frame:
                if first_frame is None:
                    first_frame = frame
                frame.config(bg=MISSING_BG)
                for child in frame.winfo_children():
                    try:
                        child.config(bg=MISSING_BG, activebackground=MISSING_BG)
                    except Exception:
                        pass
                    for inner in child.winfo_children():
                        try:
                            inner.config(bg=MISSING_BG, activebackground=MISSING_BG)
                        except Exception:
                            pass

        if first_frame:
            canvas.update_idletasks()
            bbox = canvas.bbox("all")
            if bbox:
                target_y = first_frame.winfo_rooty() - scroll_area.winfo_rooty()
                total_height = max(1, bbox[3] - bbox[1])
                canvas.yview_moveto(max(0, min(1, target_y / total_height)))

    def go_back():
        app.show_my_evaluations()

    def save_draft():
        answers = {}
        for cq_id, var in answers_vars.items():
            if var.get() > 0:
                answers[cq_id] = var.get()

        if not answers:
            messagebox.showwarning("Incomplete", "Please answer at least one question before saving.")
            return

        comment_value = comment_text.get("1.0", "end").strip()

        if save_evaluation_answers(evaluation_id, answers, comment_value):
            messagebox.showinfo("Saved", "Evaluation draft saved successfully.")
            app.show_my_evaluations()
        else:
            messagebox.showerror("Error", "Failed to save evaluation draft.")

    def submit_now():
        answers = {}
        missing = []

        for cq_id, var in answers_vars.items():
            if var.get() == 0:
                missing.append(cq_id)
            else:
                answers[cq_id] = var.get()

        if missing:
            highlight_missing_rows(missing)
            messagebox.showwarning(
                "Incomplete",
                "Please answer all questions before submitting."
            )
            return

        reset_row_highlights()
        comment_value = comment_text.get("1.0", "end").strip()

        if not save_evaluation_answers(evaluation_id, answers, comment_value):
            messagebox.showerror("Error", "Failed to save answers.")
            return

        if submit_evaluation(evaluation_id):
            messagebox.showinfo("Submitted", "Evaluation submitted successfully.")
            app.show_my_evaluations()
        else:
            messagebox.showerror("Error", "Failed to submit evaluation.")

    styled_button(
        right_actions, "Back", NEUTRAL, NEUTRAL_HOVER, go_back
    ).pack(side="left", padx=(0, 10))

    if not preview:
        styled_button(
            right_actions, "Save Draft", NEUTRAL, NEUTRAL_HOVER, save_draft
        ).pack(side="left", padx=(0, 10))

        styled_button(
            right_actions, "Submit Evaluation", ACCENT, ACCENT_HOVER, submit_now
        ).pack(side="left")


def show_preview_evaluation(app, subject_item):
    show_evaluation_form(app, subject_item, preview=True)