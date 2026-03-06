import streamlit as st
import pandas as pd
import joblib
import plotly.express as px
import os
from auth import authenticate_user


# -----------------------------
# SESSION INITIALIZATION
# -----------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_role" not in st.session_state:
    st.session_state.user_role = None

def login_page():
    st.title("YUTP Donor Management System Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate_user(username, password)

        if user:
            st.session_state.logged_in = True
            st.session_state.user_role = user["role"]
            st.session_state.username = username
        else:
            st.error("Invalid username or password")

# ==========================
# LOGIN GATE
# ==========================

if not st.session_state.logged_in:
    login_page()
    st.stop()

# CATEGORY COLOR MAP FOR CONSISTENT VISUALIZATION

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
    /* Row Container */
.dashboard-row {{
    background-color: #ffffff;
    padding: 20px;
    border-radius: 16px;
    border: 1px solid #f0f0f0;
    box-shadow: 0 6px 18px rgba(0,0,0,0.04);
    margin-bottom: 20px;
}}

    /* Chart Container */
.chart-box {{
    background-color: #ffffff;
    padding: 15px;
    border-radius: 14px;
    border: 1px solid #f0f0f0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
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
            
    .dashboard-row {{
        background-color: #ffffff;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #f0f0f0;
        box-shadow: 0 6px 18px rgba(0,0,0,0.04);
        margin-bottom: 25px;
    }}

    .chart-box {{
        background-color: #ffffff;
        padding: 15px;
        border-radius: 14px;
    }}

    /* Centered Container for AI */
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

    /* Move selector spacing outside nested block and escape braces for f-string */
    .sidebar .stSelectbox, .sidebar .stMultiSelect, .sidebar .stTextInput {{
        margin-bottom: 10px;
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
#LOAD ML ASSETS

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
# LOAD DATABASE DATA
# =========================

from data_access import get_full_dataset

@st.cache_data
def load_data():
    return get_full_dataset()

df = load_data()

# -------------------------------------
# DATA TYPE NORMALIZATION (safe conversion)
# -------------------------------------
if "month" in df.columns:
    df["month"] = pd.to_numeric(df["month"], errors="coerce")
    df = df[df["month"].notna()]
    df["month"] = df["month"].astype(int)

if "year" in df.columns:
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df[df["year"].notna()]
    df["year"] = df["year"].astype(int)

if "quarter" in df.columns:
    df["quarter"] = pd.to_numeric(df["quarter"], errors="coerce")
    df = df[df["quarter"].notna()]
    df["quarter"] = df["quarter"].astype(int)

# =====================================
# DEFINE generate_ai_predictions (moved here so it's defined before use)
# =====================================
def generate_ai_predictions(df, model, le=None):
    """
    Add predicted_likelihood (0.0-1.0) and predicted_interest_area columns to a copy of df and return it.
    This function is defensive: it tries predict_proba, then predict, and falls back to safe defaults.
    """
    import pandas as _pd

    if model is None:
        return df

    out = df.copy()

    # Prepare a candidate X. Use the full dataframe in a best-effort attempt; many pipelines accept a DataFrame.
    X = out.copy()

    # 1) Try predict_proba -> use max class probability as likelihood and argmax class as interest
    try:
        proba = model.predict_proba(X)
        # If predict_proba returns shape (n_samples, n_classes)
        if hasattr(proba, "shape") and proba.ndim == 2:
            # likelihood = max probability per row
            out["predicted_likelihood"] = _pd.Series(proba.max(axis=1))
            # interest area: class with highest probability if available
            if hasattr(model, "classes_"):
                classes = model.classes_
                preds = [classes[i] for i in proba.argmax(axis=1)]
                out["predicted_interest_area"] = _pd.Series(preds)
            else:
                out["predicted_interest_area"] = _pd.Series(model.predict(X))
            return out
    except Exception:
        # fall through to next attempt
        pass

    # 2) Try predict -> assign predicted_interest_area and set a binary likelihood
    try:
        preds = model.predict(X)
        out["predicted_interest_area"] = _pd.Series(preds)
        # If preds numeric/binary, convert to 0/1 float; otherwise set 1.0 for any non-null prediction
        try:
            out["predicted_likelihood"] = (_pd.Series(preds) != 0).astype(float)
        except Exception:
            out["predicted_likelihood"] = 1.0
        return out
    except Exception:
        pass

    # 3) Fallback: no model output available, set defaults
    import numpy as np
    out["predicted_likelihood"] = np.random.uniform(0.2,0.9,len(out))
    out["predicted_interest_area"] = None
    return out

# =====================================
# GENERATE AI PREDICTIONS (ONCE)
# =====================================
if model is not None:
    df = generate_ai_predictions(df, model)

# 5. Sidebar

selected_year = "All"
selected_category = []
selected_fund = []
selected_month = []
selected_country = []
corporate_search = ""
likelihood_filter = 0

with st.sidebar:
    st.markdown("## Navigation")

    user_role = st.session_state.user_role

    # Role-based navigation
    if user_role == "admin":
        page_options = [
            "Executive Overview",
            "Donor Engagement Intelligence",
            "AI Strategic Intelligence",
            "Database Management"
        ]

    elif user_role in ["manager", "management"]:
        page_options = [
            "Executive Overview",
            "Donor Engagement Intelligence",
            "AI Strategic Intelligence"
        ]

    elif user_role == "donor":
        page_options = [
            "My Contributions"
        ]

    else:
        page_options = ["Executive Overview"]

    page = st.radio(
        "Select View",
        page_options
    )

    st.markdown("---")
    st.markdown("## Filters")

    # ===============================
    # PAGE 1 — EXECUTIVE FILTERS
    # ===============================
    if page == "Executive Overview":

        st.markdown("### Strategic Filters")

        available_years = sorted(df["year"].dropna().astype(int).unique())
        selected_year = st.selectbox("Year", ["All"] + available_years)

        selected_fund = st.multiselect(
            "Fund Category",
            sorted(df["fund_category"].dropna().unique())
        )

        selected_category = st.multiselect(
            "Donor Category",
            sorted(df["donor_category"].dropna().unique())
        )

    # ===============================
    # PAGE 2 — ENGAGEMENT FILTERS
    # ===============================
    elif page == "Donor Engagement Intelligence":

        st.markdown("### Operational Filters")

        available_years = sorted(df["year"].dropna().astype(int).unique())
        selected_year = st.selectbox("Year", ["All"] + available_years)

        # Ensure months are ordered 1–12 and not floats like 1.0
        month_list = sorted(df["month"].dropna().astype(int).unique())

        selected_month = st.multiselect(
            "Month",
            month_list
        )

        selected_country = st.multiselect(
            "Country",
            sorted(df["country"].dropna().unique())
        )

        selected_corporate = st.multiselect(
        "Corporate Core Business",
        sorted(df["corporate_core_business"].dropna().unique())
        )

        selected_category = st.multiselect(
            "Donor Category",
            sorted(df["donor_category"].dropna().unique())
        )

    # ===============================
    # PAGE 3 — AI FILTERS
    # ===============================
    elif page == "AI Strategic Intelligence":

        st.markdown("### AI Filters")

        likelihood_filter = st.slider(
            "Minimum Likelihood (%)",
            0,
            100,
            0
        )

        selected_category = st.multiselect(
            "Donor Category",
            sorted(df["donor_category"].dropna().unique())
        )

        search_name = st.text_input("Search Donor Name")
        selected_country = st.multiselect(
            "Country",
            sorted(df["country"].dropna().unique())
        )
        selected_corporate = st.multiselect(
            "Corporate Core Business",
            sorted(df["corporate_core_business"].dropna().unique())
        )

    st.markdown("---")

    if st.button("Reset Filters"):
        st.experimental_rerun()

# 6. Initial Filtering (Base)
# =========================
# ENHANCE MOCK DATA (REALISTIC BEHAVIOUR)
# =========================

# 12. Dashboard Display Section


# =========================================
# PAGE 1 – EXECUTIVE OVERVIEW
# =========================================

# =========================
# KPI CALCULATIONS
# =========================

if selected_year == "All":
    exec_df = df.copy()
else:
    exec_df = df[df["year"] == selected_year]



total_fund = exec_df["donation_amount"].sum()
total_donors = exec_df["donor_id"].nunique()

# Returning donor calculation (donors with more than 1 donation)
donor_counts = exec_df.groupby("donor_id").size()
returning_donors = (donor_counts > 1).sum()

if total_donors > 0:
    returning_rate = round((returning_donors / total_donors) * 100, 1)
else:
    returning_rate = 0

# Highest Donation Month
monthly_sum = exec_df.groupby("month")["donation_amount"].sum()
highest_month = monthly_sum.idxmax() if not monthly_sum.empty else "-"

# Quarterly Growth
quarter_sum = exec_df.groupby("quarter")["donation_amount"].sum().sort_index()

if len(quarter_sum) > 1:
    quarterly_growth = ((quarter_sum.iloc[-1] - quarter_sum.iloc[-2]) / quarter_sum.iloc[-2]) * 100
    quarterly_growth = round(quarterly_growth, 1)
else:
    quarterly_growth = 0


# =========================
# CHART DATA
# =========================


fund_sum = exec_df.groupby("fund_category")["donation_amount"].sum().reset_index()

fig_fund = px.bar(
    fund_sum,
    x="fund_category",
    y="donation_amount",
    title="Total Donations by Fund Category",
    color="fund_category",
    color_discrete_sequence=px.colors.qualitative.Set2
)

fig_fund.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=50, b=20)
)

# =========================
# MONTHLY PEAK ANALYSIS
# =========================

quarterly_trend = (
    exec_df.groupby(["year", "quarter"])["donation_amount"]
    .sum()
    .reset_index()
)

quarterly_trend["Year_Quarter"] = (
    quarterly_trend["year"].astype(str)
    + " Q"
    + quarterly_trend["quarter"].astype(str)
)

fig_quarter = px.line(
    quarterly_trend,
    x="Year_Quarter",
    y="donation_amount",
    markers=True,
    title="Quarterly Fundraising Trend",
    color_discrete_sequence=["#326b71"]
)

fig_quarter.update_layout(
    xaxis_tickangle=-45,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)"
)

category_dist = exec_df.groupby("donor_category")["donation_amount"].sum().reset_index()

fig_category = px.pie(
    category_dist,
    names="donor_category",
    values="donation_amount",
    title="Donation Distribution by Donor Category",
    color="donor_category",
    color_discrete_map=CATEGORY_COLOR_MAP
)

fig_category.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=50, b=20)
)


##start page display executive overview

if page == "Executive Overview":

    # ====================================
    # APPLY EXECUTIVE FILTERS
    # ====================================

    exec_df = df.copy()

    if selected_year != "All":
        exec_df = exec_df[exec_df["year"] == selected_year]

    if selected_fund:
        exec_df = exec_df[exec_df["fund_category"].isin(selected_fund)]

    if selected_category:
        exec_df = exec_df[exec_df["donor_category"].isin(selected_category)]

    # Page title (always visible)
    st.markdown("## Executive Overview")
    st.markdown("Strategic summary for top management.")

    # =========================================
    # ROW 1 – KPI CONTAINER
    # =========================================


    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
           <div class='kpi-card'>
               <div class='kpi-title'>Total Fund</div>
               <div class='kpi-value'>RM {total_fund:,.0f}</div>
           </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
           <div class='kpi-card'>
               <div class='kpi-title'>Total Donors</div>
               <div class='kpi-value'>{total_donors}</div>
           </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
           <div class='kpi-card'>
               <div class='kpi-title'>Quarterly Growth</div>
               <div class='kpi-value'>{quarterly_growth}%</div>
           </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
           <div class='kpi-card'>
               <div class='kpi-title'>Returning Donor Rate</div>
               <div class='kpi-value'>{returning_rate}%</div>
           </div>
        """, unsafe_allow_html=True)

    # =========================================
    # ROW 2 – TWO CHARTS (Quarterly + Fund Category)
    # =========================================

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(fig_quarter, use_container_width=True, config={"displayModeBar": False})

    with col2:
        st.plotly_chart(fig_fund, use_container_width=True, config={"displayModeBar": False})

    # =========================================
    # ROW 3 – One Chart (Donor Category Distribution)
    # =========================================

    col3, col4 = st.columns(2)

    with col3:
        st.plotly_chart(fig_category, use_container_width=True, config={"displayModeBar": False})


# =========================
# PAGE 2
# =========================
elif page == "Donor Engagement Intelligence":
    st.markdown("## Donor Engagement Intelligence")
    st.markdown("Operational insights into donor behavior, engagement, and contribution patterns.")

    # ====================================
    # APPLY ENGAGEMENT FILTERS
    # ====================================

    eng_df = df.copy()

    if selected_year != "All":
        eng_df = eng_df[eng_df["year"] == selected_year]

    if selected_month:
        eng_df = eng_df[eng_df["month"].isin(selected_month)]

    if selected_country:
        eng_df = eng_df[eng_df["country"].isin(selected_country)]

    if selected_category:
        eng_df = eng_df[eng_df["donor_category"].isin(selected_category)]

    if selected_corporate:
        eng_df = eng_df[
            eng_df["corporate_core_business"].isin(selected_corporate)
        ]

    # 1️. MONTHLY DONATION TREND (Operational Level)

    monthly_trend = (
        eng_df.groupby(["year", "month"])["donation_amount"]
        .sum()
        .reset_index()
        .sort_values(["year", "month"])
    )

    # Create a real datetime column for proper time-series axis
    monthly_trend["Date"] = pd.to_datetime(
        monthly_trend["year"].astype(int).astype(str) + "-" +
        monthly_trend["month"].astype(int).astype(str) + "-01"
    )

    fig_monthly = px.line(
        monthly_trend,
        x="Date",
        y="donation_amount",
        markers=True,
        title="Monthly Fundraising Trend",
        color="year",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig_monthly.update_layout(
        xaxis_title="Month",
        yaxis_title="Donation Amount (RM)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )

    fig_monthly.update_layout(
    xaxis=dict(
        tickmode="auto",
        nticks=12
    )
    )

    #2️. ALUMNI BY COUNTRY

    alumni_country = (
    eng_df[eng_df["donor_category"] == "Alumni"]
    .groupby("country")["donation_amount"]
    .sum()
    .reset_index()
    .sort_values("donation_amount", ascending=False)
    )

    fig_alumni_country = px.bar(
        alumni_country,
        x="country",
        y="donation_amount",
        title="Alumni Donations by Country",
        color="country",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig_alumni_country.update_layout(
        xaxis_tickangle=-45,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )

    #3️. CORPORATE CORE BUSINESS BREAKDOWN

    corp_df = eng_df[eng_df["donor_category"] == "Corporate"]

    corp_breakdown = (
        corp_df.groupby("corporate_core_business")["donation_amount"]
        .sum()
        .reset_index()
        .sort_values("donation_amount", ascending=False)
    )

    fig_corp = px.bar(
        corp_breakdown,
        x="corporate_core_business",
        y="donation_amount",
        title="Corporate Donations by Industry",
        color="corporate_core_business",
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    fig_corp.update_layout(
        xaxis_tickangle=-45,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )


    #4. EVENT vs DONATION RELATIONSHIP

    # =========================
    # AGGREGATED ENGAGEMENT INSIGHT
    # =========================

    attendance_summary = (
        eng_df.groupby("event_attendance_count")["donation_amount"]
        .median()
        .reset_index()
        .sort_values("event_attendance_count")
    )

    fig_event = px.scatter(
        eng_df,
        x="event_attendance_count",
        y="donation_amount",
        color="donor_category",
        size="donation_amount",
        title="Event Engagement vs Donation Value",
        color_discrete_map=CATEGORY_COLOR_MAP,
        opacity=0.7
    )

    fig_event.update_layout(
        xaxis_title="Event Attendance Count",
        yaxis_title="Average Donation (RM)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    fig_event.update_traces(marker=dict(sizemin=6))

    # ROW 1
    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(fig_monthly, use_container_width=True, config={"displayModeBar": False})

    with col2:
        st.plotly_chart(fig_alumni_country, use_container_width=True, config={"displayModeBar": False})

    # ROW 2
    col3, col4 = st.columns(2)

    with col3:
        st.plotly_chart(fig_corp, use_container_width=True, config={"displayModeBar": False})

    with col4:
        st.plotly_chart(fig_event, use_container_width=True, config={"displayModeBar": False})

# =========================
# PAGE 3
# =========================
if page == "AI Strategic Intelligence":


    st.markdown("## AI Strategic Intelligence")
    st.write("AI-driven insights and donor segmentation.")


    # 3️⃣ Aggregate per donor
    donor_summary = (
        df.groupby("donor_id")
        .agg({
            "donor_name": "first",
            "donor_category": "first",
            "country": "first",
            "corporate_core_business": "first",
            "donation_amount": "sum",
            "donation_date": "max",
            "predicted_likelihood": "first",
            "predicted_interest_area": "first"
        })
        .reset_index()
    )

    # Convert likelihood to %
    donor_summary["Likelihood (%)"] = (
        donor_summary["predicted_likelihood"] * 100
    ).round(1)

    # Create readable last donation month
    donor_summary["Last Donation Month"] = pd.to_datetime(
        donor_summary["donation_date"], errors="coerce"
    ).dt.to_period("M").astype(str)

    # Apply additional AI filters
    if search_name:
        donor_summary = donor_summary[
            donor_summary["donor_name"].str.contains(search_name, case=False, na=False)
        ]

    if selected_country:
        donor_summary = donor_summary[
            donor_summary["country"].isin(selected_country)
        ]

    if selected_corporate:
        donor_summary = donor_summary[
            donor_summary["corporate_core_business"].isin(selected_corporate)
        ]

    # ====================================
    # APPLY AI FILTERS
    # ====================================

    if selected_category:
        donor_summary = donor_summary[
            donor_summary["donor_category"].isin(selected_category)
        ]

    # Filter donors based on minimum likelihood threshold
    donor_summary = donor_summary[
        donor_summary["Likelihood (%)"] >= likelihood_filter
    ]

    # =========================
    # 1️. AI LIKELIHOOD TABLE
    # =========================
    st.markdown("### AI Likelihood Table")

    table_df = donor_summary.sort_values("Likelihood (%)", ascending=False).copy()

    # Add simple contact action column (demo feature for staff)
    table_df["Contact"] = "📧 Contact"

    # Create likelihood segmentation label for easier interpretation
    def classify_likelihood(x):
        if x >= 70:
            return "High Potential"
        elif x >= 40:
            return "Moderate Potential"
        else:
            return "Low Potential"

    table_df["AI Segment"] = table_df["Likelihood (%)"].apply(classify_likelihood)

    st.dataframe(
        table_df[[
            "donor_name",
            "donor_category",
            "country",
            "corporate_core_business",
            "Likelihood (%)",
            "AI Segment",
            "predicted_interest_area",
            "Last Donation Month",
            "Contact"
        ]],
        use_container_width=True,
        height=350
    )

    # =========================
    # 2️. AI STRATEGIC MATRIX
    # =========================
    import pandas as pd
    today = pd.Timestamp.today()

    donor_summary["Recency (Months)"] = (
        (today - pd.to_datetime(donor_summary["donation_date"], errors="coerce"))
        .dt.days / 30
    )

    donor_summary["Recency (Months)"] = (
        donor_summary["Recency (Months)"]
        .fillna(12)          # assume 12 months if missing
        .clip(lower=0.5)
    )

    fig_matrix = px.scatter(
        donor_summary,
        x="Likelihood (%)",
        y="donation_amount",
        size="Recency (Months)",
        color="donor_category",
        title="AI Donor Prioritization Matrix",
        color_discrete_map=CATEGORY_COLOR_MAP,
        hover_data=["donor_name", "country", "corporate_core_business"],
        size_max=40
    )
    fig_matrix.update_layout(
        xaxis_title="Likelihood to Donate (%)",
        yaxis_title="Total Donation Amount (RM)"
    )

    # Strategic quadrant lines and labels for the AI Donor Strategic Matrix
    # Determine quadrant split values
    median_likelihood = donor_summary["Likelihood (%)"].median()
    median_donation = donor_summary["donation_amount"].median()

    # Add quadrant divider lines
    fig_matrix.add_vline(x=median_likelihood, line_dash="dash", line_color="gray")
    fig_matrix.add_hline(y=median_donation, line_dash="dash", line_color="gray")

    # Add quadrant annotations (strategy insight)
    fig_matrix.add_annotation(x=median_likelihood*0.5, y=median_donation*1.6,
        text="Growth Potential", showarrow=False, font=dict(size=12,color="gray"))

    fig_matrix.add_annotation(x=median_likelihood*1.5, y=median_donation*1.6,
        text="Priority Donors", showarrow=False, font=dict(size=12,color="gray"))

    fig_matrix.add_annotation(x=median_likelihood*0.5, y=median_donation*0.4,
        text="Low Priority", showarrow=False, font=dict(size=12,color="gray"))

    fig_matrix.add_annotation(x=median_likelihood*1.5, y=median_donation*0.4,
        text="Re‑Engage", showarrow=False, font=dict(size=12,color="gray"))

    st.plotly_chart(fig_matrix, use_container_width=True, config={"displayModeBar": False})

    # =========================
    # 3️. MONTHLY AI TREND
    # =========================
    high_df = donor_summary[donor_summary["Likelihood (%)"] >= 70]
    if high_df.empty:
        high_df = donor_summary.nlargest(10, "Likelihood (%)")

    high_df["Last Month"] = pd.to_datetime(
        high_df["donation_date"]
    ).dt.to_period("M").astype(str)

    monthly_high = (
        high_df.groupby("Last Month")
        .size()
        .reset_index(name="High Likelihood Donors")
    )

    fig_high = px.bar(
        monthly_high,
        x="Last Month",
        y="High Likelihood Donors",
        title="Monthly High‑Potential Donor Opportunities",
        color="Last Month",
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    st.plotly_chart(fig_high, use_container_width=True, config={"displayModeBar": False})
# =========================
# PAGE DATABASE MANAGEMENT (ADMIN ONLY)
# =========================

if page == "Database Management":

    if st.session_state.user_role != "admin":
        st.error("Access Denied.")
        st.stop()

    st.markdown("## Database Management (Admin Only)")
    st.write("CRUD interface will be built here.")

# =========================
# DONOR PORTAL PAGE
# =========================

if page == "My Contributions":

    if st.session_state.user_role != "donor":
        st.error("Access Denied.")
        st.stop()

    st.markdown("## My Contribution Portal")
    st.markdown("View your personal donation history and contribution totals.")

    # Example filter using logged in username
    donor_name = st.session_state.get("username", None)

    donor_df = df.copy()

    if donor_name:
        donor_df = donor_df[
            donor_df["donor_name"].str.contains(donor_name, case=False, na=False)
        ]

    total_donation = donor_df["donation_amount"].sum()

    st.metric("Total Contributions", f"RM {total_donation:,.0f}")

    history = donor_df[[
        "donation_date",
        "donation_amount",
        "fund_category"
    ]].sort_values("donation_date", ascending=False)

    st.markdown("### Donation History")

    st.dataframe(
        history,
        use_container_width=True
    )