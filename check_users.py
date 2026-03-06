from database import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT username, role FROM users")
users = cursor.fetchall()

for user in users:
    print(dict(user))

conn.close()