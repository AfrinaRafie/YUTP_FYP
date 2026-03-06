import pandas as pd
from database import get_connection


def get_full_dataset():
    conn = get_connection()

    query = """
    SELECT 
        d.donor_id,
        d.donor_name,
        d.donor_category,
        d.country,
        d.donor_relationship_age_months,
        d.is_hnwi,
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
        e.last_event_date,

        ap.predicted_likelihood,
        ap.predicted_interest_area

    FROM donors d
    LEFT JOIN donations dn ON d.donor_id = dn.donor_id
    LEFT JOIN donor_engagement e ON d.donor_id = e.donor_id
    LEFT JOIN ai_predictions ap ON d.donor_id = ap.donor_id
    """

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df