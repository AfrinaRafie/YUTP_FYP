from database import get_connection

def update_user_role(username, new_role):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET role = ?
        WHERE username = ?
    """, (new_role, username))

    conn.commit()
    conn.close()

    print(f"Role updated to '{new_role}' for user '{username}'")

if __name__ == "__main__":
    update_user_role("admin", "admin")