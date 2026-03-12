import bcrypt
from db_connection import get_connection


def is_bcrypt_hash(password_value: str) -> bool:
    if not password_value:
        return False

    return (
        password_value.startswith("$2a$")
        or password_value.startswith("$2b$")
        or password_value.startswith("$2y$")
    )


def login_user(email, password):
    conn = get_connection()

    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, email, password, user_type, is_active
            FROM users
            WHERE email = %s
            LIMIT 1
        """, (email,))

        user = cursor.fetchone()

        if not user:
            return None

        if int(user["is_active"]) != 1:
            return None

        stored_password = user["password"] or ""

        # If password is bcrypt hash
        if is_bcrypt_hash(stored_password):
            if bcrypt.checkpw(password.encode(), stored_password.encode()):
                return user
            return None

        # Fallback for old plain-text passwords
        if stored_password == password:
            return user

        return None

    finally:
        cursor.close()
        conn.close()