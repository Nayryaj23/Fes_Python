import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
from db_connection import get_connection
from auth import login_user
from Admin.Dashboard import DashboardApp
from Students.student_dashboard import StudentDashboardApp

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ================= COLORS =================
BG_MAIN = "#f7f2f2"
CARD_OUTER = "#ead6d6"
LEFT_BG = "#ffffff"
RIGHT_BG = "#e7c6c6"
ACCENT = "#8b4a4a"
ACCENT_HOVER = "#723939"
TEXT_DARK = "#4a2c2c"
TEXT_MUTED = "#7c5f5f"
TEXT_SOFT = "#a17f7f"
TEXT_LIGHT = "#ffffff"
ENTRY_BG = "#fffdfd"
ENTRY_BORDER = "#cfaeae"
WHITE = "#ffffff"


# ================= HELPERS =================
def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


def open_login():
    login_file = os.path.join(os.getcwd(), "login.py")
    subprocess.Popen([sys.executable, login_file])


def get_user_full_name(user_id):
    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT first_name, middle_name, last_name
            FROM user_profiles
            WHERE user_id = %s
            LIMIT 1
        """, (user_id,))
        profile = cursor.fetchone()

        if not profile:
            return None

        first_name = profile["first_name"] or ""
        middle_name = profile["middle_name"] or ""
        last_name = profile["last_name"] or ""

        full_name = f"{first_name} {middle_name} {last_name}".strip()
        full_name = " ".join(full_name.split())
        return full_name if full_name else None

    finally:
        conn.close()


def focus_in_entry(frame):
    frame.config(highlightbackground=ACCENT, highlightcolor=ACCENT)


def focus_out_entry(frame):
    frame.config(highlightbackground=ENTRY_BORDER, highlightcolor=ACCENT)


def toggle_password():
    if password_entry.cget("show") == "":
        password_entry.config(show="*")
        eye_btn.config(text="👁")
    else:
        password_entry.config(show="")
        eye_btn.config(text="◡")


def on_login_hover(event):
    login_btn.config(bg=ACCENT_HOVER)


def on_login_leave(event):
    login_btn.config(bg=ACCENT)


def forgot_password():
    messagebox.showinfo(
        "Forgot Password",
        "Please contact the system administrator to reset your password."
    )


# ================= DASHBOARD WINDOWS =================
def open_admin_dashboard(user):
    root.destroy()

    admin_root = tk.Tk()
    admin_root.title("Admin Dashboard")
    admin_root.state("zoomed")

    DashboardApp(admin_root)
    admin_root.mainloop()


def open_student_dashboard(user):
    root.destroy()

    student_root = tk.Tk()
    app = StudentDashboardApp(student_root, student_id=user["id"])
    student_root.mainloop()


def open_faculty_dashboard(user):
    root.destroy()

    faculty_root = tk.Tk()
    faculty_root.title("Faculty Dashboard")
    faculty_root.configure(bg="#f7f3f3")
    center_window(faculty_root, 1100, 700)

    topbar = tk.Frame(faculty_root, bg="#6d3b3b", height=70)
    topbar.pack(fill="x")
    topbar.pack_propagate(False)

    tk.Label(
        topbar,
        text="Faculty Dashboard",
        font=("Segoe UI", 20, "bold"),
        fg="white",
        bg="#6d3b3b"
    ).pack(side="left", padx=20, pady=15)

    tk.Label(
        topbar,
        text=f"Welcome, {user['full_name']}",
        font=("Segoe UI", 11),
        fg="white",
        bg="#6d3b3b"
    ).pack(side="right", padx=20)

    content = tk.Frame(faculty_root, bg="#fffafa")
    content.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(
        content,
        text="You are logged in as Faculty.",
        font=("Segoe UI", 18, "bold"),
        fg="#4a2c2c",
        bg="#fffafa"
    ).pack(pady=(40, 10))

    tk.Label(
        content,
        text="This is your faculty dashboard area.",
        font=("Segoe UI", 11),
        fg="#7a5c5c",
        bg="#fffafa"
    ).pack()

    def logout():
        confirm = messagebox.askyesno("Logout", "Are you sure you want to logout?")
        if confirm:
            faculty_root.destroy()
            open_login()

    tk.Button(
        content,
        text="Logout",
        font=("Segoe UI", 10, "bold"),
        bg=ACCENT,
        fg="white",
        relief="flat",
        command=logout
    ).pack(pady=20)

    faculty_root.mainloop()


# ================= LOGIN =================
def login():
    email = email_entry.get().strip()
    password = password_entry.get().strip()

    if not email or not password:
        messagebox.showwarning("Missing Fields", "Please enter your email and password.")
        return

    user = login_user(email, password)

    if not user:
        messagebox.showerror("Login Failed", "Invalid email or password.")
        return

    full_name = get_user_full_name(user["id"]) or user["email"]

    logged_in_user = {
        "id": user["id"],
        "email": user["email"],
        "user_type": user["user_type"],
        "full_name": full_name,
    }

    if user["user_type"] == "admin":
        messagebox.showinfo("Login Successful", f"Welcome, {full_name}!")
        open_admin_dashboard(logged_in_user)

    elif user["user_type"] == "student":
        messagebox.showinfo("Login Successful", f"Welcome, {full_name}!")
        open_student_dashboard(logged_in_user)

    elif user["user_type"] == "faculty":
        messagebox.showinfo("Login Successful", f"Welcome, {full_name}!")
        open_faculty_dashboard(logged_in_user)

    else:
        messagebox.showerror("Login Failed", f"Unknown user role: {user['user_type']}")


# ================= MAIN WINDOW =================
root = tk.Tk()
root.title("FES Login")
root.configure(bg=BG_MAIN)
root.resizable(False, False)
center_window(root, 1020, 600)

main_frame = tk.Frame(root, bg=BG_MAIN)
main_frame.pack(fill="both", expand=True, padx=24, pady=24)

outer_card = tk.Frame(main_frame, bg=CARD_OUTER, bd=0, highlightthickness=0)
outer_card.place(relx=0.5, rely=0.5, anchor="center", width=950, height=520)

card_frame = tk.Frame(outer_card, bg=WHITE, bd=0, highlightthickness=0)
card_frame.place(relx=0.5, rely=0.5, anchor="center", width=940, height=510)

# ================= LEFT PANEL =================
left_frame = tk.Frame(card_frame, bg=LEFT_BG, width=360, height=510)
left_frame.pack(side="left", fill="y")
left_frame.pack_propagate(False)

logo_container = tk.Frame(left_frame, bg=LEFT_BG)
logo_container.place(relx=0.5, rely=0.30, anchor="center")

if PIL_AVAILABLE:
    try:
        logo = Image.open("resources/LogoSPC.png")
        logo = logo.resize((150, 150))
        logo_img = ImageTk.PhotoImage(logo)

        logo_label = tk.Label(logo_container, image=logo_img, bg=LEFT_BG)
        logo_label.pack()
    except Exception:
        tk.Label(
            logo_container,
            text="FES",
            font=("Segoe UI", 34, "bold"),
            fg=TEXT_DARK,
            bg=LEFT_BG
        ).pack()
else:
    tk.Label(
        logo_container,
        text="FES",
        font=("Segoe UI", 34, "bold"),
        fg=TEXT_DARK,
        bg=LEFT_BG
    ).pack()

tk.Label(
    left_frame,
    text="Faculty Evaluation System",
    font=("Segoe UI", 18, "bold"),
    fg=TEXT_DARK,
    bg=LEFT_BG
).place(relx=0.5, rely=0.54, anchor="center")

tk.Label(
    left_frame,
    text="School Portal Access",
    font=("Segoe UI", 11, "bold"),
    fg=ACCENT,
    bg=LEFT_BG
).place(relx=0.5, rely=0.60, anchor="center")

tk.Label(
    left_frame,
    text="Simple, secure, and elegant login interface",
    font=("Segoe UI", 10),
    fg=TEXT_MUTED,
    bg=LEFT_BG
).place(relx=0.5, rely=0.66, anchor="center")

tk.Label(
    left_frame,
    text="Manage evaluations, access records,\nand continue your work with ease.",
    font=("Segoe UI", 10),
    fg=TEXT_SOFT,
    bg=LEFT_BG,
    justify="center"
).place(relx=0.5, rely=0.74, anchor="center")

# ================= RIGHT PANEL =================
right_frame = tk.Frame(card_frame, bg=RIGHT_BG, width=580, height=510)
right_frame.pack(side="right", fill="both", expand=True)
right_frame.pack_propagate(False)

tk.Label(
    right_frame,
    text="Welcome Back",
    font=("Segoe UI", 24, "bold"),
    fg=TEXT_DARK,
    bg=RIGHT_BG
).place(relx=0.5, y=68, anchor="center")

tk.Label(
    right_frame,
    text="Please sign in to your account",
    font=("Segoe UI", 11),
    fg=TEXT_MUTED,
    bg=RIGHT_BG
).place(relx=0.5, y=105, anchor="center")

form_x = 105
form_width = 370

tk.Label(
    right_frame,
    text="Email Address",
    font=("Segoe UI", 11, "bold"),
    fg=TEXT_DARK,
    bg=RIGHT_BG
).place(x=form_x, y=155)

email_frame = tk.Frame(
    right_frame,
    bg=ENTRY_BG,
    highlightthickness=1,
    highlightbackground=ENTRY_BORDER,
    highlightcolor=ACCENT,
    bd=0
)
email_frame.place(x=form_x, y=185, width=form_width, height=42)

email_entry = tk.Entry(
    email_frame,
    font=("Segoe UI", 12),
    bg=ENTRY_BG,
    fg=TEXT_DARK,
    bd=0,
    relief="flat",
    insertbackground=TEXT_DARK
)
email_entry.pack(fill="both", expand=True, padx=12, pady=8)
email_entry.bind("<FocusIn>", lambda e: focus_in_entry(email_frame))
email_entry.bind("<FocusOut>", lambda e: focus_out_entry(email_frame))

tk.Label(
    right_frame,
    text="Password",
    font=("Segoe UI", 11, "bold"),
    fg=TEXT_DARK,
    bg=RIGHT_BG
).place(x=form_x, y=248)

password_frame = tk.Frame(
    right_frame,
    bg=ENTRY_BG,
    highlightthickness=1,
    highlightbackground=ENTRY_BORDER,
    highlightcolor=ACCENT,
    bd=0
)
password_frame.place(x=form_x, y=278, width=form_width, height=42)

password_entry = tk.Entry(
    password_frame,
    font=("Segoe UI", 12),
    bg=ENTRY_BG,
    fg=TEXT_DARK,
    bd=0,
    relief="flat",
    show="*",
    insertbackground=TEXT_DARK
)
password_entry.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=8)
password_entry.bind("<FocusIn>", lambda e: focus_in_entry(password_frame))
password_entry.bind("<FocusOut>", lambda e: focus_out_entry(password_frame))

eye_btn = tk.Button(
    password_frame,
    text="👁",
    font=("Segoe UI", 12),
    bd=0,
    bg=ENTRY_BG,
    fg=TEXT_DARK,
    activebackground=ENTRY_BG,
    activeforeground=TEXT_DARK,
    cursor="hand2",
    command=toggle_password
)
eye_btn.pack(side="right", padx=10)

forgot_btn = tk.Label(
    right_frame,
    text="Forgot Password?",
    font=("Segoe UI", 10, "underline"),
    fg=ACCENT,
    bg=RIGHT_BG,
    cursor="hand2"
)
forgot_btn.place(x=form_x + 250, y=330)
forgot_btn.bind("<Button-1>", lambda e: forgot_password())

login_btn = tk.Button(
    right_frame,
    text="Login",
    font=("Segoe UI", 12, "bold"),
    bg=ACCENT,
    fg=TEXT_LIGHT,
    activebackground=ACCENT_HOVER,
    activeforeground=TEXT_LIGHT,
    relief="flat",
    bd=0,
    cursor="hand2",
    command=login
)
login_btn.place(x=form_x, y=365, width=form_width, height=45)
login_btn.bind("<Enter>", on_login_hover)
login_btn.bind("<Leave>", on_login_leave)

root.bind("<Return>", lambda e: login())

tk.Label(
    right_frame,
    text="Secure access for authorized users only",
    font=("Segoe UI", 9),
    fg=TEXT_SOFT,
    bg=RIGHT_BG
).place(relx=0.5, y=440, anchor="center")

root.mainloop()