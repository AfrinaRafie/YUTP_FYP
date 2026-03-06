import sqlite3
import os
DB_NAME = "yutp_donor_system.db"
print("Using database at:", os.path.abspath(DB_NAME))

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # DONORS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS donors (
        donor_id INTEGER PRIMARY KEY,
        donor_name TEXT,
        donor_category TEXT,
        country TEXT,
        donor_relationship_age_months INTEGER,
        is_hnwi TEXT,
        corporate_core_business TEXT
    )
    """)

    # DONOR ENGAGEMENT TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS donor_engagement (
        engagement_id INTEGER PRIMARY KEY,
        donor_id INTEGER,
        event_attendance_count INTEGER,
        last_event_date DATE,
        FOREIGN KEY (donor_id) REFERENCES donors(donor_id)
    )
    """)

    # DONATIONS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS donations (
        transaction_id INTEGER PRIMARY KEY,
        donor_id INTEGER,
        donation_amount REAL,
        fund_category TEXT,
        campaign_id TEXT,
        donation_date DATE,
        year INTEGER,
        month TEXT,
        quarter TEXT,
        FOREIGN KEY (donor_id) REFERENCES donors(donor_id)
    )
    """)

    # AI PREDICTIONS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_predictions (
        prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        donor_id INTEGER,
        predicted_likelihood REAL,
        predicted_interest_area TEXT,
        model_version TEXT,
        last_calculated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (donor_id) REFERENCES donors(donor_id)
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    print("Tables created successfully.")

