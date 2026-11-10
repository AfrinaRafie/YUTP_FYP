import pandas as pd

# Load the original Excel file
file = "YUTP_Donor_Data_v2.xlsx"

xls = pd.ExcelFile(file)

# Load sheets
donor_master = pd.read_excel(xls, "Donor_Master")
fund_master = pd.read_excel(xls, "Fund_Category_Master")
campaign = pd.read_excel(xls, "Campaign")
donation = pd.read_excel(xls, "Donation_Transaction")
engagement = pd.read_excel(xls, "Donor_Engagement")
ai_pred = pd.read_excel(xls, "AI_Prediction")

# -----------------------------------
# ADD EVENT COLUMNS
# -----------------------------------

# Map Campaign_ID → Campaign_Name
campaign_map = campaign.set_index("Campaign_ID")["Campaign_Name"].to_dict()

donation["event_name"] = donation["Campaign_ID"].map(campaign_map)

# Event year (copy from Year column)
donation["event_year"] = donation["Year"]

# -----------------------------------
# SAVE NEW FILE
# -----------------------------------

with pd.ExcelWriter("YUTP_Donor_Data_v2_UPDATED.xlsx") as writer:
    donor_master.to_excel(writer, sheet_name="Donor_Master", index=False)
    fund_master.to_excel(writer, sheet_name="Fund_Category_Master", index=False)
    campaign.to_excel(writer, sheet_name="Campaign", index=False)
    donation.to_excel(writer, sheet_name="Donation_Transaction", index=False)
    engagement.to_excel(writer, sheet_name="Donor_Engagement", index=False)
    ai_pred.to_excel(writer, sheet_name="AI_Prediction", index=False)

print("Dataset updated successfully.")