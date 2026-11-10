# auth.py

import hashlib
from database import get_connection

import re

def is_staff_email(username):
    """
    Validate that staff/admin users log in using a UTP work email.
    Example: name@utp.my
    """
    pattern = r"^[A-Za-z0-9._%+-]+@utp\.my$"
    return re.match(pattern, username) is not None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, role):
    conn = get_connection()
    cursor = conn.cursor()

    # Ensure staff accounts use UTP email
    if role in ("admin", "manager") and not is_staff_email(username):
        raise ValueError("Staff accounts must use a @utp.my email address")

    password_hash = hash_password(password)

    cursor.execute("""
        INSERT INTO users (username, password_hash, role)
        VALUES (?, ?, ?)
    """, (username, password_hash, role))

    conn.commit()
    conn.close()

 # Staff/Admin login uses @utp.my email stored in the users table
def authenticate_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()

    password_hash = hash_password(password)

    cursor.execute("""
        SELECT * FROM users
        WHERE username = ? AND password_hash = ?
    """, (username, password_hash))

    user = cursor.fetchone()
    conn.close()

    return user