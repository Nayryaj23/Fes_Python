import os
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox
from email.mime.text import MIMEText
import smtplib

import pandas as pd

from db_connection import get_connection

CARD_BG = "#ffffff"
CONTENT_BG = "#fffafa"
TEXT_DARK = "#4a2c2c"
TEXT_MUTED = "#7a5c5c"
ACCENT = "#8b4a4a"
ACCENT_HOVER = "#723939"
BORDER = "#eadede"
ENTRY_BG = "#fffdfd"
SUCCESS = "#2e7d32"
ERROR = "#c62828"


# =========================================================
# EMAIL CONFIG
# =========================================================
# Replace these with your real email settings if you want email sending.
SMTP_SERVER = "sandbox.smtp.mailtrap.io"
SMTP_PORT = 2525
SENDER_EMAIL = "623465e754849e"
SENDER_PASSWORD = "6d28f36707a381"
LOGIN_URL = "http://localhost/fes/login"   # change if needed


# =========================================================
# REQUIRED EXCEL COLUMNS
# =========================================================
REQUIRED_COLUMNS = [
    "school_year",
    "semester",
    "department_name",
    "program_name",
    "year_level",
    "section_name",
    "student_no",
    "student_first_name",
    "student_middle_name",
    "student_last_name",
    "student_email",
    "student_sex",
    "faculty_employee_no",
    "faculty_first_name",
    "faculty_middle_name",
    "faculty_last_name",
    "faculty_email",
    "subject_code",
    "descriptive_title",
    "units",
    "class_schedule",
]


# =========================================================
# HELPERS
# =========================================================
def normalize(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_email(value):
    return normalize(value).lower()


def safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def normalize_sex(value):
    val = normalize(value).lower()
    if val in ["male", "female", "other"]:
        return val
    return None


def default_password_for_student(student_no):
    return normalize(student_no)


def default_password_for_faculty(employee_no):
    return normalize(employee_no)


def prepare_password_for_storage(raw_password):
    """
    IMPORTANT:
    This currently stores the password as plain text so it matches simple existing login systems.
    If your login already uses hashing, replace this with your hash function.
    """
    return raw_password


def send_credentials_email(recipient_email, full_name, login_email, temp_password):
    subject = "Faculty Evaluation System Account"

    body = f"""Hello {full_name},

Your account for the Faculty Evaluation System has been created.

Login Credentials:
Email: {login_email}
Temporary Password: {temp_password}

Login URL:
{LOGIN_URL}

Please change your password after logging in.

Thank you.
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient_email

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)
    server.quit()


# =========================================================
# DATABASE LOOKUP / CREATE HELPERS
# =========================================================
def get_one(cursor, query, params):
    cursor.execute(query, params)
    return cursor.fetchone()


def find_or_create_department(cursor, name, stats):
    row = get_one(cursor, "SELECT id FROM departments WHERE name = %s", (name,))
    if row:
        return row[0]

    cursor.execute(
        "INSERT INTO departments (name) VALUES (%s)",
        (name,)
    )
    stats["departments_created"] += 1
    return cursor.lastrowid


def find_or_create_program(cursor, department_id, name, stats):
    row = get_one(
        cursor,
        "SELECT id FROM programs WHERE department_id = %s AND name = %s",
        (department_id, name)
    )
    if row:
        return row[0]

    cursor.execute("""
        INSERT INTO programs (department_id, name, created_at, updated_at)
        VALUES (%s, %s, NOW(), NOW())
    """, (department_id, name))
    stats["programs_created"] += 1
    return cursor.lastrowid


def find_or_create_section(cursor, program_id, year_level, section_name, stats):
    row = get_one(
        cursor,
        """
        SELECT id
        FROM sections
        WHERE program_id = %s AND year_level = %s AND section_name = %s
        """,
        (program_id, year_level, section_name)
    )
    if row:
        return row[0]

    cursor.execute("""
        INSERT INTO sections (program_id, year_level, section_name, created_at, updated_at)
        VALUES (%s, %s, %s, NOW(), NOW())
    """, (program_id, year_level, section_name))
    stats["sections_created"] += 1
    return cursor.lastrowid


def find_or_create_school_year(cursor, year_label, stats):
    row = get_one(cursor, "SELECT id FROM school_years WHERE year_label = %s", (year_label,))
    if row:
        return row[0]

    cursor.execute(
        "INSERT INTO school_years (year_label) VALUES (%s)",
        (year_label,)
    )
    stats["school_years_created"] += 1
    return cursor.lastrowid


def find_or_create_semester(cursor, name, stats):
    row = get_one(cursor, "SELECT id FROM semesters WHERE name = %s", (name,))
    if row:
        return row[0]

    cursor.execute(
        "INSERT INTO semesters (name) VALUES (%s)",
        (name,)
    )
    stats["semesters_created"] += 1
    return cursor.lastrowid


def find_or_create_term(cursor, school_year_id, semester_id, stats):
    row = get_one(
        cursor,
        "SELECT id FROM terms WHERE school_year_id = %s AND semester_id = %s",
        (school_year_id, semester_id)
    )
    if row:
        return row[0]

    cursor.execute("""
        INSERT INTO terms (school_year_id, semester_id, start_date, end_date, created_at, updated_at)
        VALUES (%s, %s, NULL, NULL, NOW(), NOW())
    """, (school_year_id, semester_id))
    stats["terms_created"] += 1
    return cursor.lastrowid


def find_or_create_subject(cursor, subject_code, descriptive_title, units, stats):
    row = get_one(
        cursor,
        "SELECT id FROM subjects WHERE subject_code = %s",
        (subject_code,)
    )
    if row:
        subject_id = row[0]
        cursor.execute("""
            UPDATE subjects
            SET descriptive_title = %s,
                units = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (descriptive_title, units, subject_id))
        return subject_id

    cursor.execute("""
        INSERT INTO subjects (subject_code, descriptive_title, units, created_at, updated_at)
        VALUES (%s, %s, %s, NOW(), NOW())
    """, (subject_code, descriptive_title, units))
    stats["subjects_created"] += 1
    return cursor.lastrowid


def find_user_by_email(cursor, email):
    row = get_one(cursor, "SELECT id, user_type FROM users WHERE email = %s", (email,))
    return row


def find_student_by_student_no(cursor, student_no):
    row = get_one(cursor, "SELECT user_id FROM student_profiles WHERE student_no = %s", (student_no,))
    return row[0] if row else None


def find_faculty_by_employee_no(cursor, employee_no):
    row = get_one(cursor, "SELECT user_id FROM faculty_profiles WHERE employee_no = %s", (employee_no,))
    return row[0] if row else None


def create_user(cursor, email, raw_password, user_type):
    prepared_password = prepare_password_for_storage(raw_password)

    cursor.execute("""
        INSERT INTO users (email, password, user_type, is_active, created_at, updated_at)
        VALUES (%s, %s, %s, 1, NOW(), NOW())
    """, (email, prepared_password, user_type))
    return cursor.lastrowid


def create_user_profile(cursor, user_id, first_name, middle_name, last_name, sex):
    cursor.execute("""
        INSERT INTO user_profiles (
            user_id, first_name, middle_name, last_name, sex, birthdate, phone, address, photo_path, created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, NULL, NULL, NULL, NULL, NOW(), NOW())
    """, (user_id, first_name, middle_name or None, last_name, sex))


def create_student_profile(cursor, user_id, student_no, program_id):
    cursor.execute("""
        INSERT INTO student_profiles (user_id, student_no, program_id, created_at, updated_at)
        VALUES (%s, %s, %s, NOW(), NOW())
    """, (user_id, student_no, program_id))


def create_faculty_profile(cursor, user_id, employee_no, department_id):
    cursor.execute("""
        INSERT INTO faculty_profiles (user_id, employee_no, department_id, created_at, updated_at)
        VALUES (%s, %s, %s, NOW(), NOW())
    """, (user_id, employee_no, department_id))


def find_or_create_student_user(
    cursor, student_no, email, first_name, middle_name, last_name, sex, program_id, stats
):
    user_id = find_student_by_student_no(cursor, student_no)

    if user_id:
        stats["students_reused"] += 1
        return user_id, False, default_password_for_student(student_no)

    email_user = find_user_by_email(cursor, email)
    if email_user:
        user_id = email_user[0]
        existing_profile = get_one(
            cursor,
            "SELECT user_id FROM student_profiles WHERE user_id = %s",
            (user_id,)
        )
        if not existing_profile:
            create_student_profile(cursor, user_id, student_no, program_id)
        stats["students_reused"] += 1
        return user_id, False, default_password_for_student(student_no)

    raw_password = default_password_for_student(student_no)
    user_id = create_user(cursor, email, raw_password, "student")
    create_user_profile(cursor, user_id, first_name, middle_name, last_name, sex)
    create_student_profile(cursor, user_id, student_no, program_id)
    stats["students_created"] += 1
    return user_id, True, raw_password


def find_or_create_faculty_user(
    cursor, employee_no, email, first_name, middle_name, last_name, department_id, stats
):
    user_id = find_faculty_by_employee_no(cursor, employee_no)

    if user_id:
        stats["faculty_reused"] += 1
        return user_id, False, default_password_for_faculty(employee_no)

    email_user = find_user_by_email(cursor, email)
    if email_user:
        user_id = email_user[0]
        existing_profile = get_one(
            cursor,
            "SELECT user_id FROM faculty_profiles WHERE user_id = %s",
            (user_id,)
        )
        if not existing_profile:
            create_faculty_profile(cursor, user_id, employee_no, department_id)
        stats["faculty_reused"] += 1
        return user_id, False, default_password_for_faculty(employee_no)

    raw_password = default_password_for_faculty(employee_no)
    user_id = create_user(cursor, email, raw_password, "faculty")
    create_user_profile(cursor, user_id, first_name, middle_name, last_name, None)
    create_faculty_profile(cursor, user_id, employee_no, department_id)
    stats["faculty_created"] += 1
    return user_id, True, raw_password


def find_or_create_class_offering(cursor, term_id, subject_id, faculty_id, section_id, schedule, stats):
    row = get_one(
        cursor,
        """
        SELECT id
        FROM class_offerings
        WHERE term_id = %s
          AND subject_id = %s
          AND faculty_id = %s
          AND section_id = %s
        """,
        (term_id, subject_id, faculty_id, section_id)
    )
    if row:
        offering_id = row[0]
        cursor.execute("""
            UPDATE class_offerings
            SET schedule = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (schedule or None, offering_id))
        return offering_id

    cursor.execute("""
        INSERT INTO class_offerings (
            term_id, subject_id, faculty_id, section_id, schedule, created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
    """, (term_id, subject_id, faculty_id, section_id, schedule or None))
    stats["class_offerings_created"] += 1
    return cursor.lastrowid


def find_or_create_class_enrollment(cursor, class_offering_id, student_id, stats):
    row = get_one(
        cursor,
        """
        SELECT id
        FROM class_enrollments
        WHERE class_offering_id = %s AND student_id = %s
        """,
        (class_offering_id, student_id)
    )
    if row:
        return row[0]

    cursor.execute("""
        INSERT INTO class_enrollments (
            class_offering_id, student_id, status, created_at, updated_at
        )
        VALUES (%s, %s, 'enrolled', NOW(), NOW())
    """, (class_offering_id, student_id))
    stats["enrollments_created"] += 1
    return cursor.lastrowid


# =========================================================
# IMPORT LOGIC
# =========================================================
def validate_dataframe(df):
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    return missing


def import_excel_to_database(file_path, send_email=False, log_callback=None):
    df = pd.read_excel(file_path)

    missing_columns = validate_dataframe(df)
    if missing_columns:
        raise Exception("Missing required columns:\n- " + "\n- ".join(missing_columns))

    stats = {
        "rows_processed": 0,
        "rows_skipped": 0,
        "students_created": 0,
        "students_reused": 0,
        "faculty_created": 0,
        "faculty_reused": 0,
        "departments_created": 0,
        "programs_created": 0,
        "sections_created": 0,
        "school_years_created": 0,
        "semesters_created": 0,
        "terms_created": 0,
        "subjects_created": 0,
        "class_offerings_created": 0,
        "enrollments_created": 0,
        "emails_sent": 0,
        "errors": [],
    }

    conn = get_connection()
    if not conn:
        raise Exception("Could not connect to database.")

    cursor = conn.cursor()

    try:
        for index, row in df.iterrows():
            excel_row_no = index + 2  # because header is row 1

            try:
                school_year = normalize(row["school_year"])
                semester = normalize(row["semester"])
                department_name = normalize(row["department_name"])
                program_name = normalize(row["program_name"])
                year_level = safe_int(row["year_level"])
                section_name = normalize(row["section_name"])

                student_no = normalize(row["student_no"])
                student_first_name = normalize(row["student_first_name"])
                student_middle_name = normalize(row["student_middle_name"])
                student_last_name = normalize(row["student_last_name"])
                student_email = normalize_email(row["student_email"])
                student_sex = normalize_sex(row["student_sex"])

                faculty_employee_no = normalize(row["faculty_employee_no"])
                faculty_first_name = normalize(row["faculty_first_name"])
                faculty_middle_name = normalize(row["faculty_middle_name"])
                faculty_last_name = normalize(row["faculty_last_name"])
                faculty_email = normalize_email(row["faculty_email"])

                subject_code = normalize(row["subject_code"])
                descriptive_title = normalize(row["descriptive_title"])
                units = safe_float(row["units"], 0.0)
                class_schedule = normalize(row["class_schedule"])

                # required row-level checks
                required_values = {
                    "school_year": school_year,
                    "semester": semester,
                    "department_name": department_name,
                    "program_name": program_name,
                    "year_level": year_level,
                    "section_name": section_name,
                    "student_no": student_no,
                    "student_first_name": student_first_name,
                    "student_last_name": student_last_name,
                    "student_email": student_email,
                    "faculty_employee_no": faculty_employee_no,
                    "faculty_first_name": faculty_first_name,
                    "faculty_last_name": faculty_last_name,
                    "faculty_email": faculty_email,
                    "subject_code": subject_code,
                    "descriptive_title": descriptive_title,
                }

                missing_fields = [k for k, v in required_values.items() if v in ["", 0, None]]
                if missing_fields:
                    stats["rows_skipped"] += 1
                    stats["errors"].append(f"Row {excel_row_no}: missing required data -> {', '.join(missing_fields)}")
                    continue

                if student_sex is None:
                    stats["rows_skipped"] += 1
                    stats["errors"].append(f"Row {excel_row_no}: invalid student_sex. Use male/female/other.")
                    continue

                department_id = find_or_create_department(cursor, department_name, stats)
                program_id = find_or_create_program(cursor, department_id, program_name, stats)
                section_id = find_or_create_section(cursor, program_id, year_level, section_name, stats)

                school_year_id = find_or_create_school_year(cursor, school_year, stats)
                semester_id = find_or_create_semester(cursor, semester, stats)
                term_id = find_or_create_term(cursor, school_year_id, semester_id, stats)

                faculty_id, faculty_created_now, faculty_password = find_or_create_faculty_user(
                    cursor,
                    faculty_employee_no,
                    faculty_email,
                    faculty_first_name,
                    faculty_middle_name,
                    faculty_last_name,
                    department_id,
                    stats
                )

                student_id, student_created_now, student_password = find_or_create_student_user(
                    cursor,
                    student_no,
                    student_email,
                    student_first_name,
                    student_middle_name,
                    student_last_name,
                    student_sex,
                    program_id,
                    stats
                )

                subject_id = find_or_create_subject(
                    cursor,
                    subject_code,
                    descriptive_title,
                    units,
                    stats
                )

                class_offering_id = find_or_create_class_offering(
                    cursor,
                    term_id,
                    subject_id,
                    faculty_id,
                    section_id,
                    class_schedule,
                    stats
                )

                find_or_create_class_enrollment(
                    cursor,
                    class_offering_id,
                    student_id,
                    stats
                )

                conn.commit()
                stats["rows_processed"] += 1

                if send_email:
                    try:
                        if student_created_now:
                            send_credentials_email(
                                student_email,
                                f"{student_first_name} {student_last_name}",
                                student_email,
                                student_password
                            )
                            stats["emails_sent"] += 1

                        if faculty_created_now:
                            send_credentials_email(
                                faculty_email,
                                f"{faculty_first_name} {faculty_last_name}",
                                faculty_email,
                                faculty_password
                            )
                            stats["emails_sent"] += 1

                    except Exception as email_err:
                        stats["errors"].append(f"Row {excel_row_no}: email sending failed -> {str(email_err)}")

                if log_callback:
                    log_callback(f"Processed row {excel_row_no}")

            except Exception as row_err:
                conn.rollback()
                stats["rows_skipped"] += 1
                stats["errors"].append(f"Row {excel_row_no}: {str(row_err)}")

                if log_callback:
                    log_callback(f"Skipped row {excel_row_no}: {str(row_err)}")

        return stats

    finally:
        cursor.close()
        conn.close()


# =========================================================
# UI PAGE
# =========================================================
def show_class_data_upload_page(app):
    app.clear_content()

    if not hasattr(app, "upload_file_path_var"):
        app.upload_file_path_var = tk.StringVar()

    if not hasattr(app, "send_email_var"):
        app.send_email_var = tk.IntVar(value=0)

    app.upload_file_path_var.set("")

    wrapper = tk.Frame(app.content_frame, bg=CONTENT_BG)
    wrapper.pack(fill="both", expand=True)

    # Header
    header = tk.Frame(wrapper, bg=CONTENT_BG)
    header.pack(fill="x", pady=(0, 15))

    tk.Label(
        header,
        text="Class Data Upload",
        font=("Segoe UI", 18, "bold"),
        fg=TEXT_DARK,
        bg=CONTENT_BG
    ).pack(anchor="w")

    tk.Label(
        header,
        text="Upload Excel file for students, faculty, subjects, class offerings, and enrollments.",
        font=("Segoe UI", 10),
        fg=TEXT_MUTED,
        bg=CONTENT_BG
    ).pack(anchor="w", pady=(4, 0))

    # Card
    card = tk.Frame(
        wrapper,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=BORDER
    )
    card.pack(fill="x", pady=(0, 15))

    tk.Label(
        card,
        text="Upload File",
        font=("Segoe UI", 13, "bold"),
        fg=TEXT_DARK,
        bg=CARD_BG
    ).grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(18, 15))

    tk.Label(
        card,
        text="Selected File",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg=CARD_BG
    ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 6))

    file_entry = tk.Entry(
        card,
        textvariable=app.upload_file_path_var,
        font=("Segoe UI", 10),
        bg=ENTRY_BG,
        fg=TEXT_DARK,
        relief="solid",
        bd=1,
        width=65
    )
    file_entry.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 12), ipady=6)

    def choose_file():
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[
                ("Excel Files", "*.xlsx *.xls"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            app.upload_file_path_var.set(file_path)

    choose_btn = tk.Button(
        card,
        text="Choose File",
        font=("Segoe UI", 10, "bold"),
        bg=ACCENT,
        fg="white",
        activebackground=ACCENT_HOVER,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        width=14,
        command=choose_file
    )
    choose_btn.grid(row=2, column=2, padx=20, pady=(0, 12), ipady=4)

    send_email_check = tk.Checkbutton(
        card,
        text="Send credentials to email after account creation",
        variable=app.send_email_var,
        font=("Segoe UI", 10),
        fg=TEXT_DARK,
        bg=CARD_BG,
        activebackground=CARD_BG,
        activeforeground=TEXT_DARK,
        selectcolor=CARD_BG
    )
    send_email_check.grid(row=3, column=0, columnspan=3, sticky="w", padx=20, pady=(0, 12))

    notes_box = tk.Frame(card, bg="#f8eeee", highlightthickness=1, highlightbackground=BORDER)
    notes_box.grid(row=4, column=0, columnspan=3, sticky="ew", padx=20, pady=(0, 16))

    tk.Label(
        notes_box,
        text="Import Notes",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_DARK,
        bg="#f8eeee"
    ).pack(anchor="w", padx=12, pady=(10, 4))

    notes = [
        "Students and faculty will be created automatically if they do not exist.",
        "Default student password = student_no",
        "Default faculty password = faculty_employee_no",
        "Login credential will use the email stored in the users table.",
        "Duplicate records will be reused instead of inserted again.",
    ]
    for note in notes:
        tk.Label(
            notes_box,
            text=f"• {note}",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg="#f8eeee",
            justify="left",
            anchor="w"
        ).pack(fill="x", padx=12, pady=1)

    # Summary / Logs
    summary_card = tk.Frame(
        wrapper,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=BORDER
    )
    summary_card.pack(fill="both", expand=True)

    top_bar = tk.Frame(summary_card, bg=CARD_BG)
    top_bar.pack(fill="x", padx=18, pady=(16, 10))

    tk.Label(
        top_bar,
        text="Import Summary",
        font=("Segoe UI", 13, "bold"),
        fg=TEXT_DARK,
        bg=CARD_BG
    ).pack(side="left")

    log_box = tk.Text(
        summary_card,
        font=("Consolas", 10),
        bg="#fffdfd",
        fg=TEXT_DARK,
        relief="solid",
        bd=1,
        wrap="word",
        height=18
    )
    log_box.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    def write_log(message, color=None):
        log_box.insert("end", message + "\n")
        log_box.see("end")
        app.root.update_idletasks()

    def clear_log():
        log_box.delete("1.0", "end")

    def upload_and_import():
        file_path = app.upload_file_path_var.get().strip()

        if not file_path:
            messagebox.showwarning("No File", "Please choose an Excel file first.")
            return

        if not os.path.exists(file_path):
            messagebox.showwarning("File Not Found", "The selected file does not exist.")
            return

        clear_log()
        write_log("Starting import...")
        write_log(f"File: {file_path}")
        write_log("")

        try:
            stats = import_excel_to_database(
                file_path=file_path,
                send_email=bool(app.send_email_var.get()),
                log_callback=write_log
            )

            write_log("")
            write_log("========== IMPORT COMPLETE ==========")
            write_log(f"Rows processed: {stats['rows_processed']}")
            write_log(f"Rows skipped: {stats['rows_skipped']}")
            write_log(f"Student accounts created: {stats['students_created']}")
            write_log(f"Student accounts reused: {stats['students_reused']}")
            write_log(f"Faculty accounts created: {stats['faculty_created']}")
            write_log(f"Faculty accounts reused: {stats['faculty_reused']}")
            write_log(f"Departments created: {stats['departments_created']}")
            write_log(f"Programs created: {stats['programs_created']}")
            write_log(f"Sections created: {stats['sections_created']}")
            write_log(f"School years created: {stats['school_years_created']}")
            write_log(f"Semesters created: {stats['semesters_created']}")
            write_log(f"Terms created: {stats['terms_created']}")
            write_log(f"Subjects created: {stats['subjects_created']}")
            write_log(f"Class offerings created: {stats['class_offerings_created']}")
            write_log(f"Enrollments created: {stats['enrollments_created']}")
            write_log(f"Emails sent: {stats['emails_sent']}")

            if stats["errors"]:
                write_log("")
                write_log("========== ERRORS ==========")
                for err in stats["errors"]:
                    write_log(err)

            messagebox.showinfo("Import Finished", "Excel import completed. Check the summary below.")

        except Exception as e:
            write_log("")
            write_log("========== IMPORT FAILED ==========")
            write_log(str(e))
            write_log("")
            write_log(traceback.format_exc())
            messagebox.showerror("Import Failed", str(e))

    action_frame = tk.Frame(card, bg=CARD_BG)
    action_frame.grid(row=5, column=0, columnspan=3, sticky="e", padx=20, pady=(0, 18))

    upload_btn = tk.Button(
        action_frame,
        text="Upload & Import",
        font=("Segoe UI", 10, "bold"),
        bg=ACCENT,
        fg="white",
        activebackground=ACCENT_HOVER,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        width=16,
        command=upload_and_import
    )
    upload_btn.pack(side="left", padx=(0, 8), ipady=4)

    clear_btn = tk.Button(
        action_frame,
        text="Clear Log",
        font=("Segoe UI", 10, "bold"),
        bg="#ddd0d0",
        fg=TEXT_DARK,
        activebackground="#ccbaba",
        activeforeground=TEXT_DARK,
        relief="flat",
        bd=0,
        cursor="hand2",
        width=12,
        command=clear_log
    )
    clear_btn.pack(side="left", ipady=4)

    card.grid_columnconfigure(0, weight=1)
    card.grid_columnconfigure(1, weight=1)