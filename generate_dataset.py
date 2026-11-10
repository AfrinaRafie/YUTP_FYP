"""
generate_dataset.py
-------------------
Builds a REALISTIC simulated donor dataset for the YUTP AI Donor Dashboard.

Why: the original dataset had no behavioural patterns (every donor behaved the
same), so no model could learn anything. This generator keeps the SAME tables
and column names the dashboard already uses, but simulates donors month by month
with real-world behaviour built in:

  * Corporate / HNWI donors give large, less frequent gifts; staff give small
    regular amounts (salary deduction); students give small one-off amounts.
  * Donors who attend YUTP events give more often and stay loyal longer.
  * Donors can LAPSE (stop giving) - lapse risk is higher for students and for
    donors who have not attended events recently.
  * Seasonality: Ramadan / Zakat season, year-end giving, convocation month.
  * Random noise, so the AI cannot reach a fake 100% accuracy.

Output: a SQLite database (same schema as yutp_donor_system.db + 2 new tables
`campaigns` and `event_attendance`) and an Excel copy for inspection.

Run:  python generate_dataset.py
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_DONORS = 3000
START = pd.Timestamp("2019-01-01")
SNAPSHOT = pd.Timestamp("2026-10-31")  # "today" for the dataset

OUT_DB = Path("yutp_donor_system_v2.db")
OUT_XLSX = Path("YUTP_Donor_Data_v2_realistic.xlsx")

rng = np.random.default_rng(SEED)
MONTHS = pd.date_range(START, SNAPSHOT, freq="MS")

# ---------------------------------------------------------------------------
# 1. Reference data
# ---------------------------------------------------------------------------
CATEGORY_MIX = {"Alumni": 0.34, "Individual": 0.20, "Staff": 0.16, "Student": 0.14, "Corporate": 0.16}

COUNTRY_MIX = {"Malaysia": 0.70, "Singapore": 0.08, "Indonesia": 0.06, "Brunei": 0.05, "UAE": 0.05, "UK": 0.06}

FUNDS = ["Scholarship Bursary", "Student Development Program", "Research and Innovation", "Others"]

# Fund preference per category (Dirichlet concentration)
FUND_PREF = {
    "Alumni":     [5, 3, 1, 1],
    "Individual": [4, 2, 1, 2],
    "Staff":      [3, 3, 2, 2],
    "Student":    [2, 5, 1, 2],
    "Corporate":  [3, 2, 5, 1],
}

# Behaviour per category
#   p_month : chance of donating in a month while active
#   amt_med : median gift (RM), amt_sd: log-spread
#   churn   : monthly chance of lapsing (before adjustments)
BEHAVIOUR = {
    "Student":    dict(p_month=0.07, amt_med=30,    amt_sd=0.6, churn=0.045),
    "Staff":      dict(p_month=0.30, amt_med=100,   amt_sd=0.5, churn=0.012),
    "Alumni":     dict(p_month=0.10, amt_med=200,   amt_sd=0.8, churn=0.025),
    "Individual": dict(p_month=0.08, amt_med=300,   amt_sd=0.9, churn=0.030),
    "Corporate":  dict(p_month=0.10, amt_med=20000, amt_sd=1.0, churn=0.015),
}

CORE_BUSINESS = ["Energy", "Technology & Innovation", "Education", "Healthcare", "Sustainability",
                 "Research & Development", "Community Development", "Environment", "Social Impact"]

# Real-sounding corporate donors (parents match data_access.py corporate_parent mapping)
NAMED_CORPORATES = [
    ("PETRONAS Chemicals", "Energy", "PETRONAS"), ("PETRONAS Dagangan", "Energy", "PETRONAS"),
    ("PETRONAS Carigali", "Energy", "PETRONAS"), ("PETRONAS Foundation", "Education", "PETRONAS"),
    ("Maybank Foundation", "Social Impact", "MAYBANK"), ("Maybank Islamic", "Community Development", "MAYBANK"),
    ("CIMB Foundation", "Education", "CIMB"), ("CIMB Islamic", "Social Impact", "CIMB"),
    ("Shell Malaysia", "Energy", "SHELL"), ("Shell Foundation Malaysia", "Sustainability", "SHELL"),
    ("TNB Research", "Research & Development", "TNB"), ("TNB Foundation", "Community Development", "TNB"),
]
CORP_PREFIX = ["Nusantara", "Perdana", "Seri", "Mutiara", "Harmoni", "Global", "Tekno", "Bina", "Cahaya",
               "Delta", "Prima", "Sinar", "Mega", "Puncak", "Wawasan", "Bayu", "Kencana", "Inspira"]
CORP_SUFFIX = ["Holdings Berhad", "Sdn Bhd", "Engineering Sdn Bhd", "Technologies Sdn Bhd",
               "Resources Berhad", "Energy Sdn Bhd", "Solutions Sdn Bhd", "Group Berhad", "Industries Sdn Bhd"]

MALAY_M = ["Ahmad", "Muhammad", "Hafiz", "Amir", "Faiz", "Syafiq", "Haziq", "Iskandar", "Firdaus", "Azlan",
           "Danial", "Irfan", "Khairul", "Luqman", "Naim", "Rizal", "Shahrul", "Zulkifli", "Adam", "Hakim"]
MALAY_F = ["Nur", "Siti", "Aisyah", "Farah", "Nadia", "Hana", "Izzah", "Aina", "Syahirah", "Amira",
           "Balqis", "Damia", "Fatin", "Insyirah", "Liyana", "Mardhiah", "Najwa", "Qistina", "Sofea", "Zahra"]
MALAY_LAST = ["Abdullah", "Ismail", "Rahman", "Hassan", "Yusof", "Ibrahim", "Osman", "Hamzah", "Razak", "Aziz",
              "Salleh", "Kamal", "Hashim", "Zainal", "Mohd Nor", "Jaafar", "Mansor", "Ariffin", "Bakar", "Rashid"]
CN_SURNAME = ["Tan", "Lim", "Wong", "Lee", "Ng", "Chong", "Goh", "Teh", "Ong", "Yap", "Chan", "Low", "Koh", "Cheah", "Liew"]
CN_GIVEN = ["Wei Ming", "Mei Ling", "Kar Hoe", "Jia Hui", "Chee Keong", "Siew Yee", "Boon Hock", "Li Wen",
            "Kah Seng", "Hui Min", "Kok Leong", "Pei Shan", "Zhi Hao", "Xin Yi", "Jun Kit", "Yee Ling"]
IN_GIVEN = ["Raj", "Priya", "Suresh", "Kavitha", "Arjun", "Deepa", "Vinod", "Lakshmi", "Ganesh", "Anita",
            "Haresh", "Sangeetha", "Kumar", "Revathi", "Prakash", "Meena"]
IN_LAST = ["Nair", "Subramaniam", "Pillai", "Menon", "Krishnan", "Ramasamy", "Muthu", "Selvaraj", "Raman", "Gopal"]
INTL_GIVEN = ["James", "Emily", "Oliver", "Sophie", "Daniel", "Aisha", "Omar", "Budi", "Dewi", "Rizal", "Sarah",
              "Michael", "Hannah", "Yusuf", "Fatimah", "Andi"]
INTL_LAST = ["Carter", "Watson", "Bennett", "Turner", "Hughes", "Al Mansoori", "Al Hashimi", "Santoso", "Lestari",
             "Hakim", "Wijaya", "Clarke", "Rahmat", "Haddad"]

# Ramadan months (approx) + campaign calendar
RAMADAN = {"2019-05", "2020-04", "2020-05", "2021-04", "2021-05", "2022-04", "2023-03", "2023-04",
           "2024-03", "2024-04", "2025-03", "2026-02", "2026-03"}

CAMPAIGNS = [
    (1, "General Giving", None),
    (2, "Ramadan & Zakat Appeal", "ramadan"),
    (3, "Year-End Giving Drive", 12),
    (4, "Convocation Alumni Drive", 10),
    (5, "Scholarship Week", 6),
]

EVENTS = {  # month -> event name (held every year)
    2: "Industry Networking Night",
    5: "Charity Fun Run",
    7: "Scholarship Award Ceremony",
    10: "Alumni Homecoming",
    12: "Donor Appreciation Dinner",
}


# ---------------------------------------------------------------------------
# 2. Helpers
# ---------------------------------------------------------------------------
def person_name(country):
    if country in ("Malaysia", "Brunei"):
        r = rng.random()
        if r < 0.55:
            if rng.random() < 0.5:
                first, second = rng.choice(MALAY_M, size=2, replace=False)
                return f"{first} {second} bin {rng.choice(MALAY_LAST)}"
            first, second = rng.choice(MALAY_F, size=2, replace=False)
            return f"{first} {second} binti {rng.choice(MALAY_LAST)}"
        if r < 0.85:
            return f"{rng.choice(CN_SURNAME)} {rng.choice(CN_GIVEN)}"
        return f"{rng.choice(IN_GIVEN)} {rng.choice(IN_LAST)}"
    if rng.random() < 0.5:  # many overseas donors are Malaysian alumni living abroad
        return person_name("Malaysia")
    initial = chr(int(rng.integers(65, 91)))
    return f"{rng.choice(INTL_GIVEN)} {initial}. {rng.choice(INTL_LAST)}"


def fake_ic():
    """Fake 12-digit Malaysian-IC-style login ID (not a real IC)."""
    yy, mm, dd = rng.integers(60, 99), rng.integers(1, 13), rng.integers(1, 29)
    return f"{yy:02d}{mm:02d}{dd:02d}{rng.integers(1, 15):02d}{rng.integers(1000, 9999)}"


def seasonality(month, category):
    key = month.strftime("%Y-%m")
    f = 1.0
    if key in RAMADAN:
        f *= 1.6
    if month.month == 12:
        f *= 1.4
    if month.month == 10 and category == "Alumni":
        f *= 1.5
    if month.month == 6:
        f *= 1.15
    return f


def campaign_for(month, category):
    key = month.strftime("%Y-%m")
    if key in RAMADAN:
        return 2
    if month.month == 12:
        return 3
    if month.month == 10 and category == "Alumni":
        return 4
    if month.month == 6:
        return 5
    return 1


# ---------------------------------------------------------------------------
# 3. Donors
# ---------------------------------------------------------------------------
cats = rng.choice(list(CATEGORY_MIX), size=N_DONORS, p=list(CATEGORY_MIX.values()))
countries = rng.choice(list(COUNTRY_MIX), size=N_DONORS, p=list(COUNTRY_MIX.values()))

donors, used_names, used_logins = [], set(), set()
named_corps = list(NAMED_CORPORATES)
corp_counter = {}

for i in range(N_DONORS):
    donor_id = str(i + 1)
    cat = cats[i]
    country = "Malaysia" if cat in ("Staff", "Student") else countries[i]
    core = None

    if cat == "Corporate":
        if named_corps:
            name, core, parent = named_corps.pop(0)
            country = "Malaysia"
        else:
            while True:
                name = f"{rng.choice(CORP_PREFIX)} {rng.choice(CORP_PREFIX)} {rng.choice(CORP_SUFFIX)}"
                if name not in used_names:
                    break
            core = str(rng.choice(CORE_BUSINESS))
            parent = "CORP"
        corp_counter[parent] = corp_counter.get(parent, 0) + 1
        login = f"{parent}{corp_counter[parent]:03d}"
    else:
        name = person_name(country)
        tries = 0
        while name in used_names and tries < 200:  # keep names unique for the donor portal search
            name = person_name(country)
            tries += 1
        login = fake_ic() if cat == "Individual" else donor_id
        while login in used_logins:
            login = fake_ic()

    used_names.add(name)
    used_logins.add(login)

    is_hnwi = int((cat == "Individual" and rng.random() < 0.15) or (cat == "Alumni" and rng.random() < 0.05))

    # Join date: more donors joined recently (growth of the foundation)
    join_offset = int(len(MONTHS) * (1 - rng.power(1.6)))
    join_month = MONTHS[min(join_offset, len(MONTHS) - 1)]

    donors.append(dict(
        donor_id=donor_id, donor_name=name, donor_category=cat, country=country,
        is_hnwi=is_hnwi, corporate_core_business=core, login_id=login, join_month=join_month,
        engagement=float(rng.beta(2, 5)),               # hidden: how "engaged" this donor is
        generosity=float(rng.lognormal(0, 0.35)),        # hidden: personal gift-size multiplier
        regularity=float(rng.lognormal(0, 0.45)),        # hidden: how often they give
        fund_pref=rng.dirichlet(FUND_PREF[cat]),
    ))

# ---------------------------------------------------------------------------
# 4. Simulate month by month: events, donations, lapsing
# ---------------------------------------------------------------------------
donations, attendance = [], []

for d in donors:
    b = BEHAVIOUR[d["donor_category"]]
    active = True
    last_event = None
    last_gift = None

    for m in MONTHS[MONTHS >= d["join_month"]]:
        # --- event attendance (only in event months) ---
        if m.month in EVENTS:
            p_event = 0.04 + 0.55 * d["engagement"] * (1.0 if active else 0.35)
            if d["donor_category"] == "Corporate":
                p_event *= 1.2
            if rng.random() < min(p_event, 0.9):
                attendance.append(dict(donor_id=d["donor_id"], event_name=EVENTS[m.month],
                                       event_date=(m + pd.Timedelta(days=int(rng.integers(5, 25)))).date()))
                last_event = m
                if not active and rng.random() < 0.25:  # events can win back lapsed donors
                    active = True

        months_since_event = (m.year - last_event.year) * 12 + m.month - last_event.month if last_event is not None else 99

        if not active:
            continue

        # --- does the donor give this month? ---
        p = b["p_month"] * d["regularity"] * seasonality(m, d["donor_category"])
        if months_since_event <= 3:
            p *= 1.8
        if d["is_hnwi"]:
            p *= 0.8
        first_month = last_gift is None and m == d["join_month"]
        if first_month or rng.random() < min(p, 0.95):
            amt = rng.lognormal(np.log(b["amt_med"]), b["amt_sd"]) * d["generosity"]
            if d["is_hnwi"]:
                amt *= rng.uniform(15, 40)
            if months_since_event <= 3:
                amt *= 1.25
            amt = max(10, round(amt / 10) * 10 if amt > 200 else round(amt))
            gift_day = int(rng.integers(1, 28))
            donations.append(dict(
                donor_id=d["donor_id"], donation_amount=float(amt),
                fund_category=FUNDS[rng.choice(4, p=d["fund_pref"])],
                campaign_id=campaign_for(m, d["donor_category"]),
                donation_date=(m + pd.Timedelta(days=gift_day - 1)).date(),
            ))
            last_gift = m

        # --- lapse risk ---
        churn = b["churn"]
        churn *= np.exp(-1.2 * d["engagement"])
        churn *= 0.5 if months_since_event <= 6 else 1.3
        if d["is_hnwi"]:
            churn *= 0.6
        if last_gift is not None and (m - last_gift).days > 365:
            churn *= 1.5
        if rng.random() < churn:
            active = False

# ---------------------------------------------------------------------------
# 5. Build tables (same columns as the original database)
# ---------------------------------------------------------------------------
don_df = pd.DataFrame(donations).sort_values(["donation_date", "donor_id"]).reset_index(drop=True)
don_df.insert(0, "transaction_id", np.arange(1, len(don_df) + 1))
dates = pd.to_datetime(don_df["donation_date"])
don_df["donation_date"] = dates.dt.strftime("%Y-%m-%d")
don_df["year"], don_df["month"], don_df["quarter"] = dates.dt.year, dates.dt.month, dates.dt.quarter

att_df = pd.DataFrame(attendance)
att_df.insert(0, "attendance_id", np.arange(1, len(att_df) + 1))
att_df["event_date"] = pd.to_datetime(att_df["event_date"]).dt.strftime("%Y-%m-%d")

donor_df = pd.DataFrame(donors)
first_gift = dates.groupby(don_df["donor_id"]).min()
donor_df["first_seen"] = donor_df["donor_id"].map(first_gift).fillna(donor_df["join_month"])
donor_df["donor_relationship_age_months"] = (
    (SNAPSHOT.year - donor_df["first_seen"].dt.year) * 12 + SNAPSHOT.month - donor_df["first_seen"].dt.month
).astype(int)
donors_table = donor_df[["donor_id", "donor_name", "donor_category", "country", "donor_relationship_age_months",
                         "is_hnwi", "corporate_core_business", "login_id"]]

eng = att_df.groupby("donor_id").agg(event_attendance_count=("event_name", "size"),
                                     last_event_date=("event_date", "max")).reset_index()
eng_df = donors_table[["donor_id"]].merge(eng, on="donor_id", how="left")
eng_df["event_attendance_count"] = eng_df["event_attendance_count"].fillna(0).astype(int)
eng_df.insert(0, "engagement_id", np.arange(1, len(eng_df) + 1))

camp_df = pd.DataFrame([(c, n) for c, n, _ in CAMPAIGNS], columns=["campaign_id", "campaign_name"])

# ---------------------------------------------------------------------------
# 6. Save
# ---------------------------------------------------------------------------
if OUT_DB.exists():
    OUT_DB.unlink()
con = sqlite3.connect(OUT_DB)
cur = con.cursor()
cur.executescript("""
CREATE TABLE donors (donor_id TEXT PRIMARY KEY, donor_name TEXT, donor_category TEXT, country TEXT,
    donor_relationship_age_months INTEGER, is_hnwi INTEGER, corporate_core_business TEXT, login_id TEXT);
CREATE TABLE donations (transaction_id INTEGER PRIMARY KEY, donor_id TEXT, donation_amount REAL,
    fund_category TEXT, campaign_id INTEGER, donation_date TEXT, year INTEGER, month INTEGER, quarter INTEGER);
CREATE TABLE donor_engagement (engagement_id INTEGER PRIMARY KEY, donor_id TEXT,
    event_attendance_count INTEGER, last_event_date TEXT);
CREATE TABLE event_attendance (attendance_id INTEGER PRIMARY KEY, donor_id TEXT, event_name TEXT, event_date TEXT);
CREATE TABLE campaigns (campaign_id INTEGER PRIMARY KEY, campaign_name TEXT);
CREATE TABLE ai_predictions (donor_id TEXT PRIMARY KEY, predicted_likelihood REAL, predicted_interest_area TEXT);
CREATE TABLE users (user_id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL, role TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX idx_don_donor ON donations(donor_id);
CREATE INDEX idx_don_date ON donations(donation_date);
CREATE INDEX idx_att_donor ON event_attendance(donor_id);
""")
donors_table.to_sql("donors", con, if_exists="append", index=False)
don_df.to_sql("donations", con, if_exists="append", index=False)
eng_df.to_sql("donor_engagement", con, if_exists="append", index=False)
att_df.to_sql("event_attendance", con, if_exists="append", index=False)
camp_df.to_sql("campaigns", con, if_exists="append", index=False)
con.commit()
con.close()

try:
    with pd.ExcelWriter(OUT_XLSX) as xw:
        donors_table.to_excel(xw, sheet_name="Donor_Master", index=False)
        don_df.to_excel(xw, sheet_name="Donation_Transaction", index=False)
        eng_df.to_excel(xw, sheet_name="Donor_Engagement", index=False)
        att_df.to_excel(xw, sheet_name="Event_Attendance", index=False)
        camp_df.to_excel(xw, sheet_name="Campaign", index=False)
except ModuleNotFoundError:
    print("(openpyxl not installed - skipped Excel copy)")

print(f"Donors: {len(donors_table):,} | Donations: {len(don_df):,} | Event attendances: {len(att_df):,}")
print(f"Date range: {don_df['donation_date'].min()} -> {don_df['donation_date'].max()}")
print(f"Total raised: RM {don_df['donation_amount'].sum():,.0f}")
print(f"Saved: {OUT_DB} and {OUT_XLSX}")
