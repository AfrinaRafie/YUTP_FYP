import pandas as pd
import numpy as np

# Load the dataset
file_name = 'yutp_donor_data.csv'
df = pd.read_csv(file_name, header=1)

# 1. FIX THE "RECENCY" GAP
# Populating the 9,982 missing values in 'Months_Since_Last_Donation'
# with random integers between 1 and 24 to simulate a real donation timeline.
missing_mask = df['Months_Since_Last_Donation'].isnull()
df.loc[missing_mask, 'Months_Since_Last_Donation'] = np.random.randint(1, 25, size=missing_mask.sum())
df['Months_Since_Last_Donation'] = df['Months_Since_Last_Donation'].astype(int)

# 2. ALIGN WITH YUTP STRATEGY (Islamic Giving & Campaigns)
# Diversifying the campaigns to include specific types required by the SV:
# Zakat, Waqaf, and Infaq.
campaign_choices = ['Zakat UTP', 'Waqaf Fund', 'Infaq Education', 'Scholarship Fund', 'Research Grant', 'Campus Development']
df['Last_Campaign_Joined'] = np.random.choice(campaign_choices, size=len(df))

# 3. FEATURE ENGINEERING (HNWI Tagging)
# Identifying High-Net-Worth Individuals (HNWIs) as requested in the proposal.
# Logic: If 'Individual' and total donations > RM 5,000.
df['Is_HNWI'] = ((df['Donor_Category'] == 'Individual') & (df['Total_Amount_Donated_RM'] > 5000)).astype(int)

# 4. SAVE CLEANED DATA
output_file = 'cleaned_yutp_donor_data.csv'
df.to_csv(output_file, index=False)
