from database import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS donations")
cursor.execute("DROP TABLE IF EXISTS donors")

conn.commit()
conn.close()

print("Tables dropped successfully.")