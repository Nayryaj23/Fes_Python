import bcrypt
from db_connection import get_connection


def login_user(email, password):
    conn = get_connection()

    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id, email, password, user_type FROM users WHERE email = %s",
        (email,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        return None

    stored_hash = user["password"]

    if bcrypt.checkpw(password.encode(), stored_hash.encode()):
        return user

    return None