import pandas as pd
from database import get_connection

EXCEL_FILE = "YUTP_Donor_Data_v2.xlsx"

donor_df = pd.read_excel(EXCEL_FILE, sheet_name="Donor_Master")

print("Donor_Master Columns:")
print(donor_df.columns.tolist())

def migrate_data():
    conn = get_connection()
    cursor = conn.cursor()

    donor_df = pd.read_excel(EXCEL_FILE, sheet_name="Donor_Master")
    txn_df = pd.read_excel(EXCEL_FILE, sheet_name="Donation_Transaction")

    engagement_df = pd.read_excel(EXCEL_FILE, sheet_name="Donor_Engagement")

    txn_df["Donation_Date"] = txn_df["Donation_Date"].astype(str)

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
                corporate_core_business
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            row["Donor_ID"],
            row["Donor_Name"],
            row["Donor_Category"],
            row["Country"],
            row["Donor_Relationship_Age_Months"],
            row["Is_HNWI"],
            row["Corporate_Core_Business"]
        ))

    # Insert donations
    for _, row in txn_df.iterrows():
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
            row["Transaction_ID"],
            row["Donor_ID"],
            row["Donation_Amount_RM"],
            row["Fund_Category"],
            row["Campaign_ID"],
            str(row["Donation_Date"]),   # 🔥 FIX HERE
            row["Year"],
            row["Month"],
            row["Quarter"]
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
            row["Engagement_ID"],
            row["Donor_ID"],
            row["Event_Attendance_Count"],
            str(row["Last_Event_Date"])
        ))

    conn.commit()
    conn.close()

    print("Excel migrated successfully.")

if __name__ == "__main__":
    migrate_data()