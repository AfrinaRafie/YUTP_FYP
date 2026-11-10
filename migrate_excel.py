import pandas as pd
from database import get_connection

EXCEL_FILE = "YUTP_Donor_Data_UPDATED_MULTISHEET.xlsx"

 # Detect available sheets automatically
xls = pd.ExcelFile(EXCEL_FILE)
print("Available sheets:", xls.sheet_names)

# Try common sheet name variations
donor_sheet = None
for name in xls.sheet_names:
    if "donor" in name.lower() and "master" in name.lower():
        donor_sheet = name
        break
if donor_sheet is None:
    donor_sheet = xls.sheet_names[0]

donor_df = pd.read_excel(EXCEL_FILE, sheet_name=donor_sheet)
donor_df.columns = donor_df.columns.str.lower()

print("Donor_Master Columns:")
print(donor_df.columns.tolist())

def migrate_data():
    conn = get_connection()
    cursor = conn.cursor()
    # ---------------------------------------
    # Clear existing data to avoid duplicates
    # ---------------------------------------
    # Drop old tables if schema is outdated
    cursor.execute("DROP TABLE IF EXISTS donors")
    cursor.execute("DROP TABLE IF EXISTS donations")
    cursor.execute("DROP TABLE IF EXISTS donor_engagement")
    cursor.execute("DROP TABLE IF EXISTS ai_predictions")

    cursor.execute("""
        CREATE TABLE donors (
            donor_id TEXT PRIMARY KEY,
            donor_name TEXT,
            donor_category TEXT,
            country TEXT,
            donor_relationship_age_months INTEGER,
            is_hnwi INTEGER,
            corporate_core_business TEXT,
            login_id TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE donations (
            transaction_id INTEGER PRIMARY KEY,
            donor_id TEXT,
            donation_amount REAL,
            fund_category TEXT,
            campaign_id INTEGER,
            donation_date TEXT,
            year INTEGER,
            month INTEGER,
            quarter INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE donor_engagement (
            engagement_id INTEGER PRIMARY KEY,
            donor_id TEXT,
            event_attendance_count INTEGER,
            last_event_date TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE ai_predictions (
            donor_id TEXT,
            predicted_likelihood REAL,
            predicted_interest_area TEXT
        )
    """)

    xls = pd.ExcelFile(EXCEL_FILE)

    # Detect donor sheet
    donor_sheet = next((s for s in xls.sheet_names if "donor" in s.lower() and "master" in s.lower()), xls.sheet_names[0])

    # Detect transaction sheet
    txn_sheet = next((s for s in xls.sheet_names if "transaction" in s.lower() or "donation" in s.lower()), xls.sheet_names[1] if len(xls.sheet_names) > 1 else xls.sheet_names[0])

    # Detect engagement sheet
    eng_sheet = next((s for s in xls.sheet_names if "engagement" in s.lower()), xls.sheet_names[-1])

    donor_df = pd.read_excel(EXCEL_FILE, sheet_name=donor_sheet)
    txn_df = pd.read_excel(EXCEL_FILE, sheet_name=txn_sheet)
    engagement_df = pd.read_excel(EXCEL_FILE, sheet_name=eng_sheet)

    # Normalize column names to lowercase for consistent access
    donor_df.columns = donor_df.columns.str.lower()
    txn_df.columns = txn_df.columns.str.lower()
    engagement_df.columns = engagement_df.columns.str.lower()

    # Ensure login_id column exists and normalize values
    if "login_id" not in donor_df.columns:
        donor_df["login_id"] = donor_df["donor_id"]

    donor_df["login_id"] = (
        donor_df["login_id"]
        .fillna(donor_df["donor_id"])
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
    )

    # Also normalize donor_id to avoid Excel float issues
    donor_df["donor_id"] = (
        donor_df["donor_id"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
    )

    # Ensure donation_date is string
    if "donation_date" in txn_df.columns:
        txn_df["donation_date"] = txn_df["donation_date"].astype(str)

    # Insert donors
    for _, row in donor_df.iterrows():
        cursor.execute("""
            INSERT INTO donors (
                donor_id,
                donor_name,
                donor_category,
                country,
                donor_relationship_age_months,
                is_hnwi,
                corporate_core_business,
                login_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(row.get("donor_id")),
            row.get("donor_name"),
            row.get("donor_category"),
            row.get("country"),
            row.get("donor_relationship_age_months", 0),
            row.get("is_hnwi", 0),
            row.get("corporate_core_business"),
            str(row.get("login_id")).strip() if pd.notna(row.get("login_id")) else None
        ))

    # Insert donations
    for _, row in txn_df.iterrows():
        donation_value = row.get("donation_amount")

        # Support older dataset column name
        if donation_value is None:
            donation_value = row.get("donation_amount_rm")

        cursor.execute("""
            INSERT INTO donations (
                transaction_id,
                donor_id,
                donation_amount,
                fund_category,
                campaign_id,
                donation_date,
                year,
                month,
                quarter
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row.get("transaction_id"),
            str(row.get("donor_id")),
            donation_value,
            row.get("fund_category"),
            row.get("campaign_id"),
            str(row.get("donation_date")) if row.get("donation_date") is not None else None,
            row.get("year"),
            row.get("month"),
            row.get("quarter")
        ))
        
    # Insert donor engagement
    for _, row in engagement_df.iterrows():
        cursor.execute("""
            INSERT INTO donor_engagement (
                engagement_id,
                donor_id,
                event_attendance_count,
                last_event_date
            )
            VALUES (?, ?, ?, ?)
        """, (
            row.get("engagement_id"),
            str(row.get("donor_id")),
            row.get("event_attendance_count", 0),
            str(row.get("last_event_date")) if row.get("last_event_date") is not None else None
        ))

    conn.commit()
    conn.close()

    print("Excel migrated successfully.")

if __name__ == "__main__":
    migrate_data()