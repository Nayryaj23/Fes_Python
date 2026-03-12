import tkinter as tk
from tkinter import messagebox
from db_connection import get_connection

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


def login():
    email = email_entry.get().strip()
    password = password_entry.get().strip()

    if not email or not password:
        messagebox.showwarning("Missing Fields", "Please enter your email and password.")
        return

    conn = get_connection()
    if conn is None:
        messagebox.showerror("Connection Error", "Unable to connect to the database.")
        return

    try:
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT id, email, password, user_type, is_active
            FROM users
            WHERE email = %s
            LIMIT 1
        """
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if not user:
            messagebox.showerror("Login Failed", "Account not found.")
            return

        if int(user["is_active"]) != 1:
            messagebox.showerror("Login Failed", "This account is inactive.")
            return

        # Plain-text password check based on your current setup
        if user["password"] != password:
            messagebox.showerror("Login Failed", "Incorrect password.")
            return

        messagebox.showinfo(
            "Login Successful",
            f"Welcome!\n\nEmail: {user['email']}\nRole: {user['user_type'].title()}"
        )

    except Exception as e:
        messagebox.showerror("System Error", f"An error occurred:\n{e}")

    finally:
        conn.close()


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
    messagebox.showinfo("Forgot Password", "Please contact the system administrator to reset your password.")


def focus_in_entry(frame):
    frame.config(highlightbackground=ACCENT, highlightcolor=ACCENT)


def focus_out_entry(frame):
    frame.config(highlightbackground=ENTRY_BORDER, highlightcolor=ACCENT)


# ================= MAIN WINDOW =================
root = tk.Tk()
root.title("FES Login")
root.configure(bg=BG_MAIN)
root.resizable(False, False)
center_window(root, 1020, 600)

# ================= MAIN WRAPPER =================
main_frame = tk.Frame(root, bg=BG_MAIN)
main_frame.pack(fill="both", expand=True, padx=24, pady=24)

# Outer card to simulate soft border/shadow
outer_card = tk.Frame(main_frame, bg=CARD_OUTER, bd=0, highlightthickness=0)
outer_card.place(relx=0.5, rely=0.5, anchor="center", width=950, height=520)

# Inner main card
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
        fallback_logo = tk.Label(
            logo_container,
            text="FES",
            font=("Segoe UI", 34, "bold"),
            fg=TEXT_DARK,
            bg=LEFT_BG
        )
        fallback_logo.pack()
else:
    fallback_logo = tk.Label(
        logo_container,
        text="FES",
        font=("Segoe UI", 34, "bold"),
        fg=TEXT_DARK,
        bg=LEFT_BG
    )
    fallback_logo.pack()

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

# Header
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

# ================= EMAIL =================
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

# ================= PASSWORD =================
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

# ================= FORGOT PASSWORD =================
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

# ================= LOGIN BUTTON =================
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

# ================= FOOTER =================
# tk.Label(
#     right_frame,
#     text="Use your registered email and password",
#     font=("Segoe UI", 10),
#     fg=TEXT_MUTED,
#     bg=RIGHT_BG
# ).place(relx=0.5, y=440, anchor="center")

tk.Label(
    right_frame,
    text="Secure access for authorized users only",
    font=("Segoe UI", 9),
    fg=TEXT_SOFT,
    bg=RIGHT_BG
).place(relx=0.5, y=440, anchor="center")

root.mainloop()