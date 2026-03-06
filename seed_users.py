from database import get_connection
from auth import hash_password

conn = get_connection()
cursor = conn.cursor()

username = "admin"
password = "admin123"
role = "admin"

password_hash = hash_password(password)

cursor.execute("""
    INSERT INTO users (username, password_hash, role)
    VALUES (?, ?, ?)
""", (username, password_hash, role))

conn.commit()
conn.close()

print("Admin created using SHA256.")

cursor.execute("SELECT username, password_hash FROM users")
print(cursor.fetchall())