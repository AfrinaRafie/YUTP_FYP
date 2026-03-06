from matplotlib.pyplot import plot
import streamlit as st
import pandas as pd
import joblib
import plotly.express as px
import os

CATEGORY_COLOR_MAP = {
    "Alumni": "#122741",      # Dark navy
    "Corporate": "#326b71",   # Teal
    "Individual": "#568b87",  # Mid teal
    "Student": "#80ae9a",     # Light teal
    "Staff": "#b5d1a9"        # Very light teal
}

# 1. Page Configuration
st.set_page_config(page_title="YUTP Donor Intelligence", layout="wide", initial_sidebar_state="expanded")

# 2. Custom CSS for Styling
st.markdown(f"""
    <style>
    .main {{ background-color: #ffffff; }} 
    
    /* Sidebar Section Containers */
.sidebar-section {{
    background-color: #f3f9f8;
    padding: 12px;
    border-radius: 10px;
    border-left: 5px solid #326b71;
    margin-bottom: 12px;
}}
            
    /* Sidebar Section Containers */
.sidebar-section {{
    background-color: #f3f9f8;
    padding: 12px;
    border-radius: 10px;
    border-left: 5px solid #326b71;
    margin-bottom: 12px;
}}
    
    /* KPI Cards with Subtle Elevation */
    .kpi-card {{
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #f0f0f0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        text-align: center;
    }}
    .kpi-title {{ font-size: 12px; color: #326b71; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }}
    .kpi-value {{ font-size: 28px; color: #122741; font-weight: 800; }}

    #/* Centered Container for AI */
    .ai-container {{
        background-color: #fcfcfc;
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #80ae9a;
        margin: auto;
    }}
        /* Sidebar Filter Boxes */
    .filter-box {{
        background-color: #f5f9f8;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #326b71;
        margin-bottom: 12px;
    }}

    .filter-title {{
        font-weight: 700;
        color: #122741;
        margin-bottom: 5px;
        font-size: 14px;
    }}

    </style>
    """, unsafe_allow_html=True)

# 3. Define load_assets()

@st.cache_resource
def load_assets():
    try:
        model = joblib.load('donor_model.pkl')
        le_cat = joblib.load('category_encoder.pkl')
        return model, le_cat
    except:
        return None, None

model, le_cat = load_assets()

# 4. Load df
# =========================
# LOAD DATA EARLY
# =========================

file_path = 'YUTP_Donor_Data.csv'

if not os.path.exists(file_path):
    st.error("Missing Data Source.")
    st.stop()

df = pd.read_csv(file_path)


# 5. Sidebar
# =========================
# DEFAULT FILTER VALUES
# =========================

min_amt = int(df['Total_Amount_Donated_RM'].min())
max_amt = int(df['Total_Amount_Donated_RM'].max())
max_event = int(df['Event_Attendance_Count'].max())

if "search_name" not in st.session_state:
    st.session_state.search_name = ""

if "selected_cat" not in st.session_state:
    st.session_state.selected_cat = "All"

if "donation_range" not in st.session_state:
    st.session_state.donation_range = (min_amt, max_amt)

if "min_event" not in st.session_state:
    st.session_state.min_event = 0

if "status_filter" not in st.session_state:
    st.session_state.status_filter = ["High", "Moderate", "Low"]


# =========================
# SIDEBAR
# =========================

with st.sidebar:

    st.markdown("<h3 style='text-align: center; color: #122741;'>Dashboard Filters</h3>", unsafe_allow_html=True)
    st.markdown("---")

    # -------------------------
    # DONOR FILTER
    # -------------------------
    with st.expander("👤 Donor Filter", expanded=True):

        search_name = st.text_input(
            "Search Donor Name",
            key="search_name"
        )

        category_list = ["All", "Alumni", "Corporate", "Individual", "Student", "Staff"]
        with st.popover("Donor Category", use_container_width=True):

            # Search input
            search_cat = st.text_input("Search Category", key="cat_search")

            # Filter category list dynamically
            filtered_categories = [
                c for c in category_list 
                if search_cat.lower() in c.lower()
            ]

            # Initialize session state
            if "selected_categories" not in st.session_state:
                st.session_state.selected_categories = category_list

            # Display checkboxes
            selected = []
            for c in filtered_categories:
                checked = st.checkbox(
                    c,
                    value=c in st.session_state.selected_categories,
                    key=f"cat_{c}"
                )
                if checked:
                    selected.append(c)

            st.session_state.selected_categories = selected

    # -------------------------
    # FINANCIAL FILTER
    # -------------------------
    with st.expander("💰 Financial Filter"):

        donation_range = st.slider(
            "Donation Amount Range (RM)",
            min_amt,
            max_amt,
            key="donation_range"
        )

    # -------------------------
    # ENGAGEMENT FILTER
    # -------------------------
    with st.expander("🎟 Engagement Filter"):

        min_event = st.slider(
            "Minimum Event Attendance",
            0,
            max_event,
            key="min_event"
        )

    # -------------------------
    # AI FILTER
    # -------------------------
    with st.expander("🤖 AI Segmentation"):
        if "status_filter" not in st.session_state:
            st.session_state.status_filter = ["High", "Moderate", "Low"]

        with st.popover("AI Likelihood Status", use_container_width=True):

            status_options = ["High", "Moderate", "Low"]
            selected_status = []

            for s in status_options:
                checked = st.checkbox(
                    s,
                    value=s in st.session_state.status_filter,
                    key=f"status_{s}"
                )
                if checked:
                    selected_status.append(s)

            st.session_state.status_filter = selected_status

    st.markdown("---")

    # -------------------------
    # RESET BUTTON
    # -------------------------
    if st.button("🔄 Reset All Filters"):
        st.session_state.clear()
        st.rerun()

# 6. Initial Filtering (Base)


filtered_df = df.copy()

# Name filter
if search_name:
    filtered_df = filtered_df[
        filtered_df['Donor_Name'].str.contains(search_name, case=False)
    ]

# Category filter
if st.session_state.selected_categories:
    filtered_df = filtered_df[
        filtered_df['Donor_Category'].isin(st.session_state.selected_categories)
    ]

# Simulate Donation Date (since mock dataset)
import numpy as np
filtered_df['Donation_Date'] = pd.to_datetime(
    np.random.choice(
        pd.date_range("2024-01-01", "2024-12-31"),
        size=len(filtered_df)
    )
)

# =========================
# ENHANCE MOCK DATA (REALISTIC BEHAVIOUR)
# =========================

# Simulate richer event attendance (0–6 events)
filtered_df['Event_Attendance_Count'] = np.random.randint(0, 7, size=len(filtered_df))

# Simulate number of contributions (1–8 times)
filtered_df.loc[filtered_df['Number_of_Contributions'] == 1, 'Event_Attendance_Count'] = 0

# Simulate High Net Worth Individuals (20%)
filtered_df['Is_HNWI'] = np.random.choice([0, 1], size=len(filtered_df), p=[0.8, 0.2])



# 7. Apply Advanced Filters

# Donation Amount
filtered_df = filtered_df[
    (filtered_df['Total_Amount_Donated_RM'] >= donation_range[0]) &
    (filtered_df['Total_Amount_Donated_RM'] <= donation_range[1])
]

# Event Attendance
filtered_df = filtered_df[
    filtered_df['Event_Attendance_Count'] >= min_event
]

# AI Status (only after AI calculated)
#if 'Status' in filtered_df.columns:
 #   filtered_df = filtered_df[
 #       filtered_df['Status'].isin(st.session_state.status_filter)
 #   ]

# 8. KPI CALCULATIONS

total_fund = filtered_df['Total_Amount_Donated_RM'].sum()
total_donors = len(filtered_df)
# Returning Donor Rate (% donors with >1 contribution)
returning_rate = (
    (filtered_df['Number_of_Contributions'] > 1).mean() * 100
)

returning_rate = round(returning_rate, 1)
total_engagement = filtered_df['Event_Attendance_Count'].sum()


# 9. MONTHLY GROWTH DATA

monthly_growth = (
    filtered_df
    .groupby(filtered_df['Donation_Date'].dt.to_period("M"))['Total_Amount_Donated_RM']
    .sum()
    .reset_index()
)

monthly_growth['Donation_Date'] = monthly_growth['Donation_Date'].astype(str)


# 10. AI PREDICTION ENGINE


if model and not filtered_df.empty:

    prep_df = filtered_df.copy()
    prep_df['Donor_Category'] = le_cat.transform(prep_df['Donor_Category'])

    features = [
        'Donor_Category',
        'Donor_Relationship_Age_Months',
        'Number_of_Contributions',
        'Total_Amount_Donated_RM',
        'Months_Since_Last_Donation',
        'Event_Attendance_Count',
        'Is_HNWI'
    ]

    
    preds = model.predict_proba(prep_df[features])[:, 1]
    filtered_df['Predicted Likelihood (%)'] = (preds * 100)
    #filtered_df['Predicted Likelihood (%)'] = (preds * 100).round(1)

# -------------------------
# Percentile-Based Segmentation
# -------------------------

high_threshold = filtered_df['Predicted Likelihood (%)'].quantile(0.7)
moderate_threshold = filtered_df['Predicted Likelihood (%)'].quantile(0.4)

def set_status(score):
    if score >= high_threshold:
        return "High"
    elif score >= moderate_threshold:
        return "Moderate"
    else:
        return "Low"

filtered_df['Status'] = filtered_df['Predicted Likelihood (%)'].apply(set_status)

# Apply AI Status filter AFTER Status is created
if "status_filter" in st.session_state:
    filtered_df = filtered_df[
        filtered_df['Status'].isin(st.session_state.status_filter)
    ]

# THEN optional rounding
filtered_df['Predicted Likelihood (%)'] = (
    filtered_df['Predicted Likelihood (%)']
    .clip(0, 100)
    .round(1)
)



# 11. TOP DONORS DATA

top_donors = (
    filtered_df
    .groupby('Donor_Name')
    .agg({
        'Total_Amount_Donated_RM': 'sum',
        'Last_Campaign_Joined': 'count'
    })
    .reset_index()
    .rename(columns={
        'Total_Amount_Donated_RM': 'Total Donation (RM)',
        'Last_Campaign_Joined': 'Events Joined'
    })
    .sort_values('Total Donation (RM)', ascending=False)
    .head(10)
)


# 12. Dashboard Display Section


st.markdown("<h1 style='color: #122741; font-weight: 800;'>YUTP AI Donor Intelligence Dashboard</h1>", unsafe_allow_html=True)

# =========================================
# ROW 1 — KPI CARDS
# =========================================

high_count = filtered_df[filtered_df['Status'] == "High"].shape[0] if 'Status' in filtered_df.columns else 0

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Total Fund</div><div class='kpi-value'>RM {total_fund:,.0f}</div></div>", unsafe_allow_html=True)

with c2:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Total Donors</div><div class='kpi-value'>{total_donors}</div></div>", unsafe_allow_html=True)

with c3:
    st.markdown(
        f"<div class='kpi-card'>"
        f"<div class='kpi-title'>Returning Donor Rate</div>"
        f"<div class='kpi-value'>{returning_rate}%</div>"
        f"</div>",
        unsafe_allow_html=True
    )

with c4:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Engagement</div><div class='kpi-value'>{total_engagement}</div></div>", unsafe_allow_html=True)

with c5:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>High Priority</div><div class='kpi-value'>{high_count}</div></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================================
# ROW 2 — DONATION INTELLIGENCE (2 CHARTS)
# =========================================

col1, col2 = st.columns(2)

with col1:
    fig_growth = px.line(
        monthly_growth,
        x='Donation_Date',
        y='Total_Amount_Donated_RM',
        markers=True,
        title="Monthly Donation Growth (RM)",
        color_discrete_sequence=['#326b71']
    )
    st.plotly_chart(fig_growth, use_container_width=True)

with col2:
    category_sum = filtered_df.groupby('Donor_Category')['Total_Amount_Donated_RM'].sum().reset_index()
    fig_cat = px.bar(
    category_sum,
    x='Donor_Category',
    y='Total_Amount_Donated_RM',
    color='Donor_Category',
    color_discrete_map=CATEGORY_COLOR_MAP,
    title="Donation by Donor Category"
    )
    st.plotly_chart(fig_cat, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

#=========================================
# ROW 3 — TOP DONORS + BEHAVIOUR CHART
# =========================================

col3, col4 = st.columns(2)

with col3:
    st.markdown(" ## Top 10 Donors")

    styled_top = top_donors.style.set_properties(
        subset=["Total Donation (RM)", "Events Joined"],
        **{"text-align": "center"}
    )

    st.dataframe(
        styled_top,
        use_container_width=True,
        height=350
    )

with col4:
    fig_scatter = px.scatter(
    filtered_df,
    x='Number_of_Contributions',
    y='Total_Amount_Donated_RM',
    color='Donor_Category',
    color_discrete_map=CATEGORY_COLOR_MAP,
    size='Event_Attendance_Count',
    title="Donation Behaviour Analysis"
)

    st.plotly_chart(fig_scatter, use_container_width=True)

# =========================================
# ROW 4 — AI INTELLIGENCE SECTION
# =========================================

st.markdown("<div class='ai-container'>", unsafe_allow_html=True)
st.markdown("### 🤖 AI Donor Intelligence Engine")

ai_col1, ai_col2 = st.columns([2,1])

with ai_col1:
    display_df = filtered_df[
        ['Donor_Name', 'Donor_Category', 'Predicted Likelihood (%)', 'Status']
    ].sort_values('Predicted Likelihood (%)', ascending=False)

    # Format to 1 decimal + % symbol
    display_df["Predicted Likelihood (%)"] = display_df["Predicted Likelihood (%)"].map(
        lambda x: f"{x:.1f}%"
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        height=350
    )

with ai_col2:

    # Ensure numeric likelihood for plotting
    plot_df = filtered_df.copy()

    # If likelihood was converted to string earlier, convert back safely
    plot_df["Predicted Likelihood (%)"] = plot_df["Predicted Likelihood (%)"].astype(float)

    # Min-max scaling to visually stretch values
    min_val = plot_df["Predicted Likelihood (%)"].min()
    max_val = plot_df["Predicted Likelihood (%)"].max()

    plot_df["Likelihood_Visual"] = (
        (plot_df["Predicted Likelihood (%)"] - min_val) /
        (max_val - min_val)
    ) * 100

    # Calculate mean lines
    mean_likelihood = plot_df["Likelihood_Visual"].mean()
    mean_donation = plot_df["Total_Amount_Donated_RM"].mean()

    fig_quadrant = px.scatter(
    plot_df,
    x="Likelihood_Visual",
    y="Total_Amount_Donated_RM",
    color="Status",
    title="AI Donor Strategic Matrix",
    color_discrete_map={
        "High": "#2ecc71",
        "Moderate": "#f1c40f",
        "Low": "#e74c3c"
    },
    hover_data=["Donor_Name"]
)

    # Add vertical mean line
    fig_quadrant.add_vline(
        x=mean_likelihood,
        line_dash="dash",
        line_color="gray"
    )

    # Add horizontal mean line
    fig_quadrant.add_hline(
        y=mean_donation,
        line_dash="dash",
        line_color="gray"
    )

    st.plotly_chart(fig_quadrant, use_container_width=True)


st.markdown("</div>", unsafe_allow_html=True)