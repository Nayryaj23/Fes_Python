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


def fetch_evaluation_summary(evaluation_period_id, class_offering_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                COUNT(DISTINCT e.id) AS total_evaluations,
                ROUND(AVG(a.rating_value), 2) AS overall_average
            FROM evaluations e
            INNER JOIN evaluation_periods ep
                ON ep.id = e.evaluation_period_id
            LEFT JOIN evaluation_answers a
                ON a.evaluation_id = e.id
            LEFT JOIN criterion_questions cq
                ON cq.id = a.criterion_question_id
            LEFT JOIN criteria c
                ON c.id = cq.criterion_id
            WHERE e.status = 'submitted'
              AND ep.status = 'open'
              AND e.evaluation_period_id = %s
              AND e.class_offering_id = %s
              AND c.form_id = ep.form_id
        """

        cursor.execute(query, (evaluation_period_id, class_offering_id))
        return cursor.fetchone()

    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load evaluation summary.\n\n{e}")
        return None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def fetch_evaluation_details(evaluation_period_id, class_offering_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                c.id AS criterion_id,
                c.title AS criterion_title,
                c.position AS criterion_position,
                cq.id AS criterion_question_id,
                cq.position AS question_position,
                q.question_text,
                a.rating_value
            FROM evaluations e
            INNER JOIN evaluation_periods ep
                ON ep.id = e.evaluation_period_id
            INNER JOIN evaluation_answers a
                ON a.evaluation_id = e.id
            INNER JOIN criterion_questions cq
                ON cq.id = a.criterion_question_id
            INNER JOIN criteria c
                ON c.id = cq.criterion_id
            INNER JOIN questions q
                ON q.id = cq.question_id
            WHERE e.status = 'submitted'
              AND ep.status = 'open'
              AND e.evaluation_period_id = %s
              AND e.class_offering_id = %s
              AND c.form_id = ep.form_id
            ORDER BY
                c.position ASC,
                cq.position ASC,
                a.id ASC
        """

        cursor.execute(query, (evaluation_period_id, class_offering_id))
        rows = cursor.fetchall()

        print("DETAIL ROWS:")
        for r in rows:
            print(r)

        return rows

    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load detailed evaluation results.\n\n{e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def fetch_criterion_summary(evaluation_period_id, class_offering_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                c.id AS criterion_id,
                c.title AS criterion_title,
                c.position AS criterion_position,
                ROUND(AVG(a.rating_value), 2) AS average_rating
            FROM evaluations e
            INNER JOIN evaluation_periods ep
                ON ep.id = e.evaluation_period_id
            INNER JOIN evaluation_answers a
                ON a.evaluation_id = e.id
            INNER JOIN criterion_questions cq
                ON cq.id = a.criterion_question_id
            INNER JOIN criteria c
                ON c.id = cq.criterion_id
            WHERE e.status = 'submitted'
              AND ep.status = 'open'
              AND e.evaluation_period_id = %s
              AND e.class_offering_id = %s
              AND c.form_id = ep.form_id
            GROUP BY
                c.id,
                c.title,
                c.position
            ORDER BY
                c.position ASC
        """

        cursor.execute(query, (evaluation_period_id, class_offering_id))
        return cursor.fetchall()

    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load criterion summary.\n\n{e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def fetch_evaluation_comments(evaluation_period_id, class_offering_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT ec.comment_text
            FROM evaluations e
            INNER JOIN evaluation_periods ep
                ON ep.id = e.evaluation_period_id
            INNER JOIN evaluation_comments ec
                ON ec.evaluation_id = e.id
            WHERE e.status = 'submitted'
              AND ep.status = 'open'
              AND e.evaluation_period_id = %s
              AND e.class_offering_id = %s
            ORDER BY ec.id DESC
        """

        cursor.execute(query, (evaluation_period_id, class_offering_id))
        return cursor.fetchall()

    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load comments.\n\n{e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_verbal_interpretation(avg):
    try:
        avg = float(avg)
    except (TypeError, ValueError):
        return "No Rating"

    if avg >= 4.50:
        return "Excellent"
    elif avg >= 3.50:
        return "Very Satisfactory"
    elif avg >= 2.50:
        return "Satisfactory"
    elif avg >= 1.50:
        return "Fair"
    else:
        return "Poor"


def show_evaluation_result_page(app):
    parent = app.content_frame

    for widget in parent.winfo_children():
        widget.destroy()

    if not getattr(app, "selected_class_offering_id", None):
        empty_frame = tk.Frame(parent, bg=BG_MAIN)
        empty_frame.pack(fill="both", expand=True)

        tk.Label(
            empty_frame,
            text="No Subject Selected",
            font=("Segoe UI", 22, "bold"),
            bg=BG_MAIN,
            fg=TEXT_DARK
        ).pack(pady=(90, 10))

        tk.Label(
            empty_frame,
            text="Please select a subject first before viewing the evaluation result.",
            font=("Segoe UI", 11),
            bg=BG_MAIN,
            fg=TEXT_MUTED
        ).pack()
        return

    summary = fetch_evaluation_summary(app.active_evaluation_period_id, app.selected_class_offering_id)
    criterion_summary = fetch_criterion_summary(app.active_evaluation_period_id, app.selected_class_offering_id)
    detail_rows = fetch_evaluation_details(app.active_evaluation_period_id, app.selected_class_offering_id)
    comments = fetch_evaluation_comments(app.active_evaluation_period_id, app.selected_class_offering_id)

    total_eval = 0
    overall_avg = 0.00

    if summary:
        total_eval = summary.get("total_evaluations") or 0
        overall_avg = summary.get("overall_average") or 0.00

    overall_interpretation = get_verbal_interpretation(overall_avg)

    style = ttk.Style()
    style.theme_use("default")

    style.configure(
        "Treeview",
        background=ROW_WHITE,
        foreground=TEXT_DARK,
        rowheight=36,
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

    # HEADER
    header_frame = tk.Frame(parent, bg=BG_MAIN)
    header_frame.pack(fill="x", pady=(0, 14))

    header_top = tk.Frame(header_frame, bg=BG_MAIN)
    header_top.pack(fill="x")

    tk.Button(
        header_top,
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
        command=app.show_faculty_subjects_page
    ).pack(side="left")

    title_frame = tk.Frame(header_frame, bg=BG_MAIN)
    title_frame.pack(fill="x", pady=(12, 0))

    tk.Label(
        title_frame,
        text="Evaluation Result",
        font=("Segoe UI", 20, "bold"),
        bg=BG_MAIN,
        fg=TEXT_DARK
    ).pack(anchor="w")

    tk.Label(
        title_frame,
        text=f"Subject: {app.selected_subject_name}",
        font=("Segoe UI", 10),
        bg=BG_MAIN,
        fg=TEXT_MUTED
    ).pack(anchor="w", pady=(4, 0))

    # SUMMARY CARDS
    summary_wrap = tk.Frame(parent, bg=BG_MAIN)
    summary_wrap.pack(fill="x", pady=(0, 14))

    def create_summary_card(parent_frame, title, value, subtext=""):
        card = tk.Frame(
            parent_frame,
            bg=CARD_BG,
            bd=1,
            relief="solid",
            highlightbackground=BORDER,
            highlightthickness=1
        )
        card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(
            card,
            text=title,
            font=("Segoe UI", 10, "bold"),
            bg=CARD_BG,
            fg=TEXT_MUTED
        ).pack(anchor="w", padx=14, pady=(12, 4))

        tk.Label(
            card,
            text=str(value),
            font=("Segoe UI", 18, "bold"),
            bg=CARD_BG,
            fg=TEXT_DARK
        ).pack(anchor="w", padx=14)

        tk.Label(
            card,
            text=subtext,
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=TEXT_MUTED,
            wraplength=250,
            justify="left"
        ).pack(anchor="w", padx=14, pady=(4, 12))

        return card

    create_summary_card(summary_wrap, "Submitted Evaluations", total_eval, "Number of submitted student evaluations")
    create_summary_card(summary_wrap, "Overall Average", overall_avg, "Computed mean of all answer ratings")
    create_summary_card(summary_wrap, "Interpretation", overall_interpretation, "Based on the rating interpretation scale")

    children = summary_wrap.winfo_children()
    if children:
        children[-1].pack_configure(padx=(0, 0))

    # # FORMULA CARD
    # formula_card = tk.Frame(
    #     parent,
    #     bg=CARD_BG,
    #     bd=1,
    #     relief="solid",
    #     highlightbackground=BORDER,
    #     highlightthickness=1
    # )
    # formula_card.pack(fill="x", pady=(0, 14))
    #
    # tk.Label(
    #     formula_card,
    #     text="Rating Formula and Interpretation Scale",
    #     font=("Segoe UI", 11, "bold"),
    #     bg=CARD_BG,
    #     fg=TEXT_DARK
    # ).pack(anchor="w", padx=16, pady=(12, 6))
    #
    # tk.Label(
    #     formula_card,
    #     text="Formula: Average Rating = Sum of all rating values ÷ Total number of responses",
    #     font=("Segoe UI", 10),
    #     bg=CARD_BG,
    #     fg=TEXT_DARK
    # ).pack(anchor="w", padx=16, pady=(0, 4))
    #
    # tk.Label(
    #     formula_card,
    #     text="Scale: 4.50–5.00 = Excellent | 3.50–4.49 = Very Satisfactory | 2.50–3.49 = Satisfactory | 1.50–2.49 = Fair | 1.00–1.49 = Poor",
    #     font=("Segoe UI", 10),
    #     bg=CARD_BG,
    #     fg=TEXT_MUTED,
    #     wraplength=1200,
    #     justify="left"
    # ).pack(anchor="w", padx=16, pady=(0, 12))

    # DETAILED RESULTS - CRITERIA WITH QUESTIONS
    details_card = tk.Frame(
        parent,
        bg=CARD_BG,
        bd=1,
        relief="solid",
        highlightbackground=BORDER,
        highlightthickness=1
    )
    details_card.pack(fill="both", expand=True, pady=(0, 14))

    tk.Label(
        details_card,
        text="Criteria, Questions, and Ratings",
        font=("Segoe UI", 11, "bold"),
        bg=CARD_BG,
        fg=TEXT_DARK
    ).pack(anchor="w", padx=16, pady=(12, 6))

    tk.Label(
        details_card,
        text="Each criterion shows its overall rating together with the questions under it.",
        font=("Segoe UI", 10),
        bg=CARD_BG,
        fg=TEXT_MUTED
    ).pack(anchor="w", padx=16, pady=(0, 8))

    details_frame = tk.Frame(details_card, bg=CARD_BG)
    details_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    detail_columns = ("criterion", "criterion_rating", "question", "question_rating", "interpretation")
    detail_tree = ttk.Treeview(details_frame, columns=detail_columns, show="headings", height=16)

    detail_tree.heading("criterion", text="Criterion")
    detail_tree.heading("criterion_rating", text="Overall Rating")
    detail_tree.heading("question", text="Question")
    detail_tree.heading("question_rating", text="Question Rating")
    detail_tree.heading("interpretation", text="Interpretation")

    detail_tree.column("criterion", width=240, anchor="center")
    detail_tree.column("criterion_rating", width=130, anchor="center")
    detail_tree.column("question", width=560, anchor="w")
    detail_tree.column("question_rating", width=130, anchor="center")
    detail_tree.column("interpretation", width=170, anchor="center")

    detail_y_scroll = ttk.Scrollbar(details_frame, orient="vertical", command=detail_tree.yview)
    detail_x_scroll = ttk.Scrollbar(details_frame, orient="horizontal", command=detail_tree.xview)
    detail_tree.configure(yscrollcommand=detail_y_scroll.set, xscrollcommand=detail_x_scroll.set)

    details_frame.rowconfigure(0, weight=1)
    details_frame.columnconfigure(0, weight=1)

    detail_tree.grid(row=0, column=0, sticky="nsew")
    detail_y_scroll.grid(row=0, column=1, sticky="ns")
    detail_x_scroll.grid(row=1, column=0, sticky="ew")

    detail_tree.tag_configure("evenrow", background=ROW_WHITE)
    detail_tree.tag_configure("oddrow", background=ROW_ALT)
    detail_tree.tag_configure(
        "criterion_row",
        background="#f3e7e7",
        foreground=TEXT_DARK,
        font=("Segoe UI", 10, "bold")
    )

    if detail_rows:
        grouped_data = {}
        for row in detail_rows:
            criterion_name = row.get("criterion_title", "No Criterion")
            grouped_data.setdefault(criterion_name, []).append(row)

        criterion_avg_map = {}
        for row in criterion_summary:
            title = row.get("criterion_title", "No Criterion")
            avg = row.get("average_rating") or 0
            criterion_avg_map[title] = avg

        row_index = 0
        for criterion_name, questions in grouped_data.items():
            criterion_avg = criterion_avg_map.get(criterion_name, 0)

            first_question = True
            for question_row in questions:
                rating_value = question_row.get("rating_value") or 0
                question_text = (question_row.get("question_text") or "").strip()
                tag = "evenrow" if row_index % 2 == 0 else "oddrow"

                detail_tree.insert(
                    "",
                    "end",
                    values=(
                        criterion_name if first_question else "",
                        criterion_avg if first_question else "",
                        question_text if question_text else "No question text found",
                        rating_value,
                        get_verbal_interpretation(rating_value)
                    ),
                    tags=(tag,)
                )

                first_question = False
                row_index += 1
    else:
        detail_tree.insert(
            "",
            "end",
            values=("No data available", "", "", "", ""),
            tags=("evenrow",)
        )

    # COMMENTS
    comments_card = tk.Frame(
        parent,
        bg=CARD_BG,
        bd=1,
        relief="solid",
        highlightbackground=BORDER,
        highlightthickness=1
    )
    comments_card.pack(fill="both", expand=False)

    tk.Label(
        comments_card,
        text="Student Comments",
        font=("Segoe UI", 11, "bold"),
        bg=CARD_BG,
        fg=TEXT_DARK
    ).pack(anchor="w", padx=16, pady=(12, 6))

    tk.Label(
        comments_card,
        text="Open-ended comments submitted by students.",
        font=("Segoe UI", 10),
        bg=CARD_BG,
        fg=TEXT_MUTED
    ).pack(anchor="w", padx=16, pady=(0, 8))

    comments_text = tk.Text(
        comments_card,
        height=10,
        wrap="word",
        font=("Segoe UI", 10),
        relief="solid",
        bd=1
    )
    comments_text.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    if comments:
        has_comment = False
        for idx, row in enumerate(comments, start=1):
            comment = (row.get("comment_text") or "").strip()
            if comment:
                has_comment = True
                comments_text.insert("end", f"{idx}. {comment}\n\n")
        if not has_comment:
            comments_text.insert("end", "No comments available.")
    else:
        comments_text.insert("end", "No comments available.")

    comments_text.config(state="disabled")