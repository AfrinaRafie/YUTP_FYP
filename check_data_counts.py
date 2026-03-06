from database import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM donors")
print("Donors count:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM donations")
print("Donations count:", cursor.fetchone()[0])

conn.close()