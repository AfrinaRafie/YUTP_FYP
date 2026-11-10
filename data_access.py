import pandas as pd
from database import get_connection


def get_full_dataset():
    conn = get_connection()
    query = """
    SELECT 
        d.donor_id,
        d.login_id,
        d.donor_name,
        d.donor_category,
        d.country,
        CASE
            WHEN LOWER(d.donor_name) LIKE 'petronas%' THEN 'PETRONAS'
            WHEN LOWER(d.donor_name) LIKE 'maybank%' THEN 'Maybank'
            WHEN LOWER(d.donor_name) LIKE 'cimb%' THEN 'CIMB'
            WHEN LOWER(d.donor_name) LIKE 'shell%' THEN 'Shell'
            WHEN LOWER(d.donor_name) LIKE 'tnb%' THEN 'TNB'
            ELSE d.donor_name
        END AS corporate_parent,
        d.corporate_core_business,

        dn.transaction_id,
        dn.donation_amount,
        dn.fund_category,
        dn.campaign_id,
        dn.donation_date,
        dn.year,
        dn.month,
        dn.quarter,

        e.event_attendance_count,
        e.last_event_date
    FROM donors d
    LEFT JOIN donations dn ON d.donor_id = dn.donor_id
    LEFT JOIN donor_engagement e ON d.donor_id = e.donor_id
    """
    try:
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()