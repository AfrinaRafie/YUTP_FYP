from database import get_connection
from auth import hash_password


conn = get_connection()
cursor = conn.cursor()

# Ensure users table exists before inserting users
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password_hash TEXT,
    role TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

username = "admin@utp.my"
password = "admin123"
role = "admin"

password_hash = hash_password(password)

cursor.execute("""
    INSERT INTO users (username, password_hash, role)
    VALUES (?, ?, ?)
""", (username, password_hash, role))

# Create manager account for demo
manager_username = "manager@utp.my"
manager_password = "manager123"
manager_role = "manager"

manager_password_hash = hash_password(manager_password)

cursor.execute("""
    INSERT OR IGNORE INTO users (username, password_hash, role)
    VALUES (?, ?, ?)
""", (manager_username, manager_password_hash, manager_role))

conn.commit()


print("Admin created using SHA256.")

cursor.execute("SELECT username, password_hash FROM users")
print(cursor.fetchall())

conn.close()