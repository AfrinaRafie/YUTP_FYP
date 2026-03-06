from auth import create_user

import hashlib
from database import get_connection

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

conn = get_connection()
cursor = conn.cursor()

username = "admin"
password = "admin123"   # change if you want
role = "admin"

cursor.execute("""
INSERT INTO users (username, password_hash, role)
VALUES (?, ?, ?)
""", (
    username,
    hash_password(password),
    role
))

conn.commit()
conn.close()

print("Admin user created successfully.")


#notes :
#create_user("admin", "admin123", "admin"):
#username = "admin"
#password = "admin123"
#role = "admin"