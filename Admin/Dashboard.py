import tkinter as tk
import subprocess
import sys
import os
from tkinter import messagebox


from Admin.Pages import faculty_page
from sidebar import Sidebar

from Admin.Pages.dashboard_page import show_dashboard_page
from Admin.Pages.evaluation_form_page import show_evaluation_form_page
from Admin.Pages.criteria_page import show_criteria_page
from Admin.Pages.evaluation_page import show_evaluation_page
from Admin.Pages.question_page import show_question_page
from Admin.Pages.class_data_upload_page import show_class_data_upload_page
# from Admin.Pages.faculty_page import show_faculty_page
# from Admin.Pages.student_page import show_student_page


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


class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FES Dashboard")
        self.root.configure(bg=BG_MAIN)
        self.root.state("zoomed")

        # Shared data
        self.criteria_data = [
            {
                "name": "Teaching Effectiveness",
                "description": "Measures clarity of instruction, mastery of the lesson, and the ability to explain topics well."
            },
            {
                "name": "Classroom Management",
                "description": "Measures orderliness, discipline, time management, and class organization."
            },
            {
                "name": "Communication Skills",
                "description": "Measures how well the instructor communicates ideas, listens to students, and responds clearly."
            },
            {
                "name": "Professionalism",
                "description": "Measures punctuality, fairness, respect, and professional conduct inside and outside the classroom."
            },
            {
                "name": "Student Engagement",
                "description": "Measures how the instructor encourages participation, interaction, and active learning."
            },
            {
                "name": "Assessment Practices",
                "description": "Measures fairness of quizzes, clarity of grading, and alignment of assessments with lessons."
            },
        ]

        self.selected_criteria_index = None

        self.main_frame = tk.Frame(root, bg=BG_MAIN)
        self.main_frame.pack(fill="both", expand=True)

        self.sidebar = Sidebar(
            self.main_frame,
            title="Admin Panel",
            menu_items={
                "Main": ["Dashboard"],
                "Management": ["Evaluation Form","Criteria", "Question", "Class Data Upload", "Evaluation"],
                "People": ["Faculty", "Students"],
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
        self.page_title.pack(side="left", padx=25, pady=15)

        self.user_label = tk.Label(
            self.topbar,
            text="Welcome, Admin",
            font=("Segoe UI", 11),
            fg=TEXT_MUTED,
            bg=TOPBAR_BG
        )
        self.user_label.pack(side="right", padx=25)

        self.content_frame = tk.Frame(self.right_container, bg=CONTENT_BG)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.show_dashboard()
        self.sidebar.set_active("Dashboard")

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def handle_menu_click(self, item):
        self.page_title.config(text=item)
        self.sidebar.set_active(item)

        if item == "Dashboard":
            self.show_dashboard()
        elif item == "Evaluation Form":
            self.show_evaluation_form()
        elif item == "Criteria":
            self.show_criteria()
        elif item == "Question":
            self.show_question()
        elif item == "Class Data Upload":
            self.show_class_data_upload()
        elif item == "Evaluation":
            self.show_evaluation()
        elif item == "Faculty":
            self.show_faculty()
        elif item == "Students":
            self.show_students()
        elif item == "Logout":
            self.logout()

    def show_dashboard(self):
        self.clear_content()
        show_dashboard_page(self)

    def show_evaluation_form(self):
        self.clear_content()
        show_evaluation_form_page(self)

    def show_criteria(self):
        self.clear_content()
        show_criteria_page(self)

    def show_question(self):
        self.clear_content()
        show_question_page(self)

    def show_class_data_upload(self):
        self.clear_content()
        show_class_data_upload_page(self)

    def show_evaluation(self):
        self.clear_content()
        show_evaluation_page(self)

    def show_faculty(self):
        self.clear_content()
        show_faculty_page(self)

    def show_students(self):
        self.clear_content()
        show_student_page(self)

    def logout(self):
        confirm = messagebox.askyesno("Logout", "Are you sure you want to logout?")

        if confirm:
            # Close dashboard window
            self.root.destroy()

            # Get project root (one level above Admin)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            # Build path to login.py
            login_path = os.path.join(base_dir, "login.py")

            # Open login window again
            subprocess.Popen([sys.executable, login_path])


if __name__ == "__main__":
    root = tk.Tk()
    center_window(root, 1280, 720)
    app = DashboardApp(root)
    root.mainloop()