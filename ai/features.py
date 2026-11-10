"""
ai/features.py
--------------
ONE place that turns raw donor data into model features.

Both the training script and the dashboard use this file, so the model always
sees features calculated exactly the same way.

Key rule (no data leakage): features only use data ON OR BEFORE the `cutoff`
date. The target ("did the donor give again?") only uses data AFTER the cutoff.
"""

import sqlite3

import numpy as np
import pandas as pd

CATEGORIES = ["Alumni", "Corporate", "Individual", "Staff", "Student"]

# Human-friendly names - used in SHAP explanations and on the dashboard
FEATURE_LABELS = {
    "recency_days": "Days since last donation",
    "frequency": "Total number of donations",
    "gifts_12m": "Donations in the last 12 months",
    "monetary_log": "Total amount donated",
    "avg_gift_log": "Average gift size",
    "amount_12m_log": "Amount donated in the last 12 months",
    "tenure_days": "Years as a donor",
    "events_total": "Events attended (all time)",
    "events_12m": "Events attended (last 12 months)",
    "days_since_event": "Days since last event",
    "campaign_share": "Share of gifts made during campaigns",
    "is_hnwi": "High-net-worth individual",
    **{f"cat_{c}": f"{c} donor" for c in CATEGORIES},
}


def load_tables(db_path):
    """Read the four tables the AI needs from SQLite."""
    con = sqlite3.connect(db_path)
    try:
        donors = pd.read_sql("SELECT * FROM donors", con)
        gifts = pd.read_sql("SELECT * FROM donations", con, parse_dates=["donation_date"])
        events = pd.read_sql("SELECT * FROM event_attendance", con, parse_dates=["event_date"])
    finally:
        con.close()
    donors["donor_id"] = donors["donor_id"].astype(str)
    gifts["donor_id"] = gifts["donor_id"].astype(str)
    events["donor_id"] = events["donor_id"].astype(str)
    return donors, gifts, events


def build_features(donors, gifts, events, cutoff):
    """Return one row of features per donor who had given on/before `cutoff`."""
    cutoff = pd.Timestamp(cutoff)
    year_ago = cutoff - pd.DateOffset(months=12)

    hist = gifts[gifts["donation_date"] <= cutoff]
    ev = events[events["event_date"] <= cutoff]

    g = hist.groupby("donor_id")
    X = pd.DataFrame({
        "recency_days": (cutoff - g["donation_date"].max()).dt.days,
        "frequency": g.size(),
        "monetary_log": np.log1p(g["donation_amount"].sum()),
        "avg_gift_log": np.log1p(g["donation_amount"].mean()),
        "tenure_days": (cutoff - g["donation_date"].min()).dt.days,
        "campaign_share": g["campaign_id"].apply(lambda s: (s != 1).mean()),
    })

    recent = hist[hist["donation_date"] > year_ago].groupby("donor_id")
    X["gifts_12m"] = recent.size().reindex(X.index, fill_value=0)
    X["amount_12m_log"] = np.log1p(recent["donation_amount"].sum().reindex(X.index, fill_value=0))

    X["events_total"] = ev.groupby("donor_id").size().reindex(X.index, fill_value=0)
    X["events_12m"] = ev[ev["event_date"] > year_ago].groupby("donor_id").size().reindex(X.index, fill_value=0)
    last_event = ev.groupby("donor_id")["event_date"].max()
    X["days_since_event"] = (cutoff - last_event).dt.days.reindex(X.index).fillna(3650)

    info = donors.set_index("donor_id")
    X["is_hnwi"] = info["is_hnwi"].reindex(X.index).fillna(0).astype(int)
    cat = info["donor_category"].reindex(X.index)
    for c in CATEGORIES:
        X[f"cat_{c}"] = (cat == c).astype(int)

    X.index.name = "donor_id"
    return X[list(FEATURE_LABELS)]


def build_targets(gifts, donor_ids, cutoff, months=12):
    """What actually happened in the `months` after the cutoff (the answers)."""
    cutoff = pd.Timestamp(cutoff)
    end = cutoff + pd.DateOffset(months=months)
    future = gifts[(gifts["donation_date"] > cutoff) & (gifts["donation_date"] <= end)]
    amount = future.groupby("donor_id")["donation_amount"].sum().reindex(donor_ids, fill_value=0.0)
    gave = (amount > 0).astype(int)
    return gave, amount
