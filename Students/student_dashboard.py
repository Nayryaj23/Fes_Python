import tkinter as tk
from tkinter import messagebox
from sidebar import Sidebar
import subprocess
import sys
import os

from Students.student_pages.dashboard_page import show_dashboard_page
from Students.student_pages.evaluations_page import show_evaluations_page
from Students.student_pages.results_page import show_results_page
from Students.student_pages.subjects_page import show_subjects_page
from Students.student_pages.profile_page import show_profile_page
from Students.student_pages.evaluation_form_page import (
    show_evaluation_form,
    show_preview_evaluation,
)

from db_connection import get_connection


BG_MAIN = "#f7f3f3"
TOPBAR_BG = "#ffffff"
CONTENT_BG = "#fffafa"
TEXT_DARK = "#4a2c2c"
TEXT_MUTED = "#7a5c5c"


def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


class StudentDashboardApp:
    def __init__(self, root, student_id):
        self.root = root
        self.student_id = student_id

        self.root.title("Student Dashboard")
        self.root.configure(bg=BG_MAIN)
        self.root.state("zoomed")

        self.student_info = {}
        self.subjects_data = []
        self.evaluations_data = []

        self.main_frame = tk.Frame(root, bg=BG_MAIN)
        self.main_frame.pack(fill="both", expand=True)

        self.sidebar = Sidebar(
            self.main_frame,
            title="Student Panel",
            menu_items={
                "Main": ["Dashboard"],
                "Evaluation": ["My Evaluations", "Results"],
                "Account": ["Profile"]
            },
            on_menu_click=self.handle_menu_click,
            bg="#6d3b3b"
        )
        self.sidebar.pack(side="left", fill="y")

        self.right_container = tk.Frame(self.main_frame, bg=BG_MAIN)
        self.right_container.pack(side="right", fill="both", expand=True)

        self.topbar = tk.Frame(self.right_container, bg=TOPBAR_BG, height=70)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)

        self.page_title = tk.Label(
            self.topbar,
            text="Dashboard",
            font=("Segoe UI", 20, "bold"),
            fg=TEXT_DARK,
            bg=TOPBAR_BG
        )
        # self.page_title.pack(side="left", padx=25, pady=15)

        self.user_label = tk.Label(
            self.topbar,
            text="Welcome, Student",
            font=("Segoe UI", 11),
            fg=TEXT_MUTED,
            bg=TOPBAR_BG
        )
        self.user_label.pack(side="right", padx=25)

        self.content_frame = tk.Frame(self.right_container, bg=CONTENT_BG)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.load_student_data()
        self.user_label.config(
            text=f"Welcome, {self.student_info.get('full_name', 'Student')}"
        )

        self.show_dashboard()
        self.sidebar.set_active("Dashboard")

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def handle_menu_click(self, item):
        self.page_title.config(text=item)

        if item == "Dashboard":
            self.sidebar.set_active(item)
            self.show_dashboard()
        elif item == "My Evaluations":
            self.sidebar.set_active(item)
            self.show_my_evaluations()
        elif item == "Results":
            self.sidebar.set_active(item)
            self.show_results()
        elif item == "Profile":
            self.sidebar.set_active(item)
            self.show_profile()
        elif item == "Logout":
            self.logout()

    def load_student_data(self):
        self.student_info = self.fetch_student_profile()
        self.subjects_data = self.fetch_student_subjects()
        self.evaluations_data = self.fetch_student_evaluations()

    def refresh_data(self):
        self.load_student_data()

    def fetch_student_profile(self):
        conn = get_connection()
        if conn is None:
            return {}

        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT 
                    u.id,
                    u.email,
                    u.is_active,
                    sp.student_no,
                    up.first_name,
                    up.middle_name,
                    up.last_name,
                    p.name AS program_name
                FROM users u
                LEFT JOIN user_profiles up ON up.user_id = u.id
                LEFT JOIN student_profiles sp ON sp.user_id = u.id
                LEFT JOIN programs p ON p.id = sp.program_id
                WHERE u.id = %s
                LIMIT 1
            """
            cursor.execute(query, (self.student_id,))
            row = cursor.fetchone()

            if not row:
                return {}

            middle = f" {row['middle_name']}" if row.get("middle_name") else ""
            full_name = f"{row.get('first_name', '')}{middle} {row.get('last_name', '')}".strip()

            return {
                "id": row["id"],
                "email": row.get("email", ""),
                "student_no": row.get("student_no", ""),
                "program_name": row.get("program_name", "N/A"),
                "full_name": full_name if full_name else "Student",
                "status": "Active" if row.get("is_active") == 1 else "Inactive"
            }

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load student profile.\n{e}")
            return {}
        finally:
            conn.close()

    def fetch_student_subjects(self):
        """
        Fetch only enrolled subjects that have an OPEN evaluation period.
        If no open evaluation period exists for the subject's term,
        it will not be shown in My Evaluations.
        """
        conn = get_connection()
        if conn is None:
            return []

        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT
                    co.id AS class_offering_id,
                    co.term_id,
                    s.subject_code,
                    s.descriptive_title,
                    CONCAT(COALESCE(up.first_name, ''), ' ', COALESCE(up.last_name, '')) AS faculty_name,
                    ep.id AS open_evaluation_period_id,
                    ep.starts_at AS evaluation_starts_at,
                    ep.ends_at AS evaluation_ends_at,
                    ep.status AS evaluation_period_status
                FROM class_enrollments ce
                INNER JOIN class_offerings co
                    ON co.id = ce.class_offering_id
                INNER JOIN subjects s
                    ON s.id = co.subject_id
                INNER JOIN users fu
                    ON fu.id = co.faculty_id
                LEFT JOIN user_profiles up
                    ON up.user_id = fu.id
                INNER JOIN evaluation_periods ep
                    ON ep.term_id = co.term_id
                   AND ep.status = 'open'
                WHERE ce.student_id = %s
                  AND ce.status = 'enrolled'
                ORDER BY s.subject_code ASC
            """
            cursor.execute(query, (self.student_id,))
            return cursor.fetchall()

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load student subjects.\n{e}")
            return []
        finally:
            conn.close()

    def fetch_student_evaluations(self):
        conn = get_connection()
        if conn is None:
            return []

        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT
                    e.id,
                    e.class_offering_id,
                    e.evaluation_period_id,
                    e.status,
                    e.submitted_at,
                    ep.starts_at,
                    ep.ends_at,
                    ep.status AS period_status,
                    s.subject_code,
                    s.descriptive_title,
                    CONCAT(COALESCE(up.first_name, ''), ' ', COALESCE(up.last_name, '')) AS faculty_name
                FROM evaluations e
                INNER JOIN evaluation_periods ep
                    ON ep.id = e.evaluation_period_id
                INNER JOIN class_offerings co
                    ON co.id = e.class_offering_id
                INNER JOIN subjects s
                    ON s.id = co.subject_id
                INNER JOIN users fu
                    ON fu.id = co.faculty_id
                LEFT JOIN user_profiles up
                    ON up.user_id = fu.id
                WHERE e.student_id = %s
                ORDER BY ep.starts_at DESC, e.created_at DESC
            """
            cursor.execute(query, (self.student_id,))
            return cursor.fetchall()

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load evaluations.\n{e}")
            return []
        finally:
            conn.close()

    def get_evaluation_for_subject(self, class_offering_id):
        matching = [
            evaluation for evaluation in self.evaluations_data
            if evaluation["class_offering_id"] == class_offering_id
        ]

        if not matching:
            return None

        return matching[0]

    def open_evaluation(self, subject_item):
        if not subject_item.get("open_evaluation_period_id"):
            messagebox.showwarning(
                "Evaluation Unavailable",
                "There is no open evaluation period for this subject."
            )
            return

        evaluation = self.get_evaluation_for_subject(subject_item["class_offering_id"])

        if evaluation and evaluation["status"] == "submitted":
            messagebox.showinfo(
                "Evaluation",
                f"You already submitted the evaluation for:\n\n"
                f"{subject_item['descriptive_title']}\n"
                f"Faculty: {subject_item['faculty_name']}"
            )
            return

        self.page_title.config(text="Evaluation Form")
        show_evaluation_form(self, subject_item, preview=False)

    def preview_evaluation(self, subject_item):
        evaluation = self.get_evaluation_for_subject(subject_item["class_offering_id"])

        if not evaluation:
            messagebox.showwarning(
                "Preview Evaluation",
                "No submitted evaluation found for this subject."
            )
            return

        self.page_title.config(text="Preview Evaluation")
        show_preview_evaluation(self, subject_item)

    def show_dashboard(self):
        self.clear_content()
        self.refresh_data()
        show_dashboard_page(self)

    def show_my_evaluations(self):
        self.clear_content()
        self.refresh_data()
        self.page_title.config(text="My Evaluations")
        show_evaluations_page(self)

    def show_results(self):
        self.clear_content()
        self.refresh_data()
        show_results_page(self)

    def show_my_subjects(self):
        self.clear_content()
        self.refresh_data()
        show_subjects_page(self)

    def show_profile(self):
        self.clear_content()
        self.refresh_data()
        show_profile_page(self)

    def logout(self):
        confirm = messagebox.askyesno("Logout", "Are you sure you want to logout?")

        if confirm:
            self.root.destroy()
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            login_path = os.path.join(base_dir, "login.py")
            subprocess.Popen([sys.executable, login_path])


if __name__ == "__main__":
    root = tk.Tk()
    app = StudentDashboardApp(root, student_id=1)
    center_window(root, 1280, 720)
    root.mainloop()