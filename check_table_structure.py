from database import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(donors)")
columns = cursor.fetchall()

print("Donors Table Structure:")
for col in columns:
    print(dict(col))   # Convert Row object to dictionary

conn.close()