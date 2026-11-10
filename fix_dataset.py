import pandas as pd
import random
import numpy as np

FILE = "YUTP_Donor_Data_v2.xlsx"

print("Loading dataset...")

xls = pd.ExcelFile(FILE)

donor_df = pd.read_excel(FILE, sheet_name="Donor_Master")
txn_df = pd.read_excel(FILE, sheet_name="Donation_Transaction")

# -----------------------------
# 1. Fix corporate donor names
# -----------------------------

corporate_names = [
"PETRONAS Carigali",
"PETRONAS Chemicals",
"PETRONAS Gas",
"PETRONAS Digital",
"PETRONAS Lubricants",
"Maybank Foundation",
"Maybank Investment Bank",
"Maybank Islamic",
"Tenaga Nasional Berhad",
"TNB Generation",
"TNB Power Services",
"Telekom Malaysia Berhad",
"TM One",
"Sime Darby Plantation",
"Sime Darby Property",
"Axiata Group Berhad",
"CelcomDigi",
"Shell Malaysia"
]

corp_idx = donor_df["Donor_Category"] == "Corporate"

donor_df.loc[corp_idx, "Donor_Name"] = [
    random.choice(corporate_names) for _ in range(corp_idx.sum())
]

# -----------------------------
# 2. Improve industry balance
# -----------------------------

industries = [
"Energy",
"Technology & Innovation",
"Finance",
"Sustainability",
"Engineering Services",
"Social Impact",
"Education",
"Healthcare",
"Environment",
"Community Development",
"Research & Development"
]

donor_df.loc[corp_idx, "Corporate_Core_Business"] = [
    random.choice(industries) for _ in range(corp_idx.sum())
]

# -----------------------------
# 3. Fix event names
# -----------------------------

events = [
"UTP Scholarship Fund Drive",
"Future Leaders Scholarship Program",
"Engineering Innovation Grant",
"Energy Sustainability Research Fund",
"UTP Alumni Giving Day",
"Industry Partnership Grant",
"Student Development Excellence Fund",
"Green Energy Research Initiative",
"UTP Research Commercialisation Fund",
"Engineering Leadership Program"
]

txn_df["Event_Name"] = [
    random.choice(events) for _ in range(len(txn_df))
]

# -----------------------------
# 4. Fix donation distribution
# -----------------------------

txn_df["Donation_Amount_RM"] = np.random.lognormal(
    mean=10.5,
    sigma=0.6,
    size=len(txn_df)
).astype(int)

print("Saving updated dataset...")

with pd.ExcelWriter("YUTP_Donor_Data_v2_FIXED.xlsx", engine="openpyxl") as writer:

    donor_df.to_excel(writer, sheet_name="Donor_Master", index=False)

    pd.read_excel(FILE, sheet_name="Fund_Category_Master")\
        .to_excel(writer, sheet_name="Fund_Category_Master", index=False)

    pd.read_excel(FILE, sheet_name="Campaign")\
        .to_excel(writer, sheet_name="Campaign", index=False)

    txn_df.to_excel(writer, sheet_name="Donation_Transaction", index=False)

    pd.read_excel(FILE, sheet_name="Donor_Engagement")\
        .to_excel(writer, sheet_name="Donor_Engagement", index=False)

    pd.read_excel(FILE, sheet_name="AI_Prediction")\
        .to_excel(writer, sheet_name="AI_Prediction", index=False)

print("Dataset fixed successfully!")