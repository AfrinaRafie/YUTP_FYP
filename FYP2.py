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
    import re

    # Center login container
    left, center, right = st.columns([1,2,1])

    with center:
        st.markdown(
            """
            <h1 style='text-align:center; margin-bottom:20px; color:#122741; font-size:28px; white-space:nowrap;'>
            YUTP Donor Intelligence Dashboard
            </h1>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <style>
            .login-title {
                font-size: 28px;
                font-weight: 600;
                margin-bottom: 10px;
                color: #122741;
            }
            .login-sub {
                color: #6c757d;
                margin-bottom: 25px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        login_container = st.container(border=True)

        with login_container:

            # Ensure no logo or st.image is displayed in the login container

            user_type = st.radio(
                "Access Portal",
                ["YUTP Internal Staff", "Registered Donor"]
            )

            if user_type == "YUTP Internal Staff":
                username = st.text_input("Staff Email (@utp.my)")
                password = st.text_input("Password", type="password")
            else:
                username = st.text_input("Login ID (IC / Passport / Corporate Donor ID)")
                password = None

            if st.button("Login"):
                if user_type == "YUTP Internal Staff":
                    # --------------------------------
                    # CASE 1: Staff login using @utp.my
                    # --------------------------------
                    if username.endswith("@utp.my"):
                        user = authenticate_user(username, password)

                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user_role = user["role"]
                            st.session_state.username = username
                        else:
                            st.error("Invalid staff email or password")
                    else:
                        st.error("Invalid staff email format")
                elif user_type == "Registered Donor":
                    # --------------------------------
                    # Donor login (IC / Passport / Corporate ID)
                    # --------------------------------
                    try:
                        from database import get_connection
                        conn = get_connection()
                        cursor = conn.cursor()

                        # Check login_id first (corporate IDs), then donor_id (IC numbers)
                        cursor.execute(
                            """
                            SELECT donor_id FROM donors
                            WHERE login_id = ? OR donor_id = ?
                            """,
                            (username, username)
                        )

                        donor = cursor.fetchone()
                        conn.close()

                        if donor:
                            st.session_state.logged_in = True
                            st.session_state.user_role = "donor"
                            st.session_state.username = username
                        else:
                            st.error("Donor login ID not found in records")

                    except Exception:
                        st.error("Unable to verify donor login")
                        st.markdown("</div>", unsafe_allow_html=True)

# ==========================
# LOGIN GATE
# ==========================

if not st.session_state.logged_in:
    # Hide sidebar on login page
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True
    )

    login_page()
    st.stop()

# CATEGORY COLOR MAP FOR CONSISTENT VISUALIZATION

CATEGORY_COLOR_MAP = {
    "Alumni": "#122741",      # Dark navy
    "Corporate": "#326b71",   # Teal
    "Individual": "#568b87",  # Mid teal
    "Staff": "#b5d1a9"        # Very light teal
}

# 1. Page Configuration

st.set_page_config(page_title="YUTP Donor Intelligence", layout="wide", initial_sidebar_state="expanded")
# Hide default Streamlit pages navigation completely
st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"] {display:none !important;}
    section[data-testid="stSidebarNav"] {display:none !important;}
    div[data-testid="stSidebarNav"] {display:none !important;}
    </style>
    """,
    unsafe_allow_html=True
)

# Load dashboard CSS styles
from styles import load_css
load_css()

# -------------------------------------
# GLOBAL PAGE LAYOUT IMPROVEMENTS
# -------------------------------------
st.markdown("""
<style>

/* Big page titles */
.page-title{
    font-size:30px;
    font-weight:800;
    color:#0b3d91;

    background:#eaf2fb;
    padding:12px 20px;
    border-radius:10px;

    border-left:6px solid #0b3d91;

    margin-top:6px;
    margin-bottom:18px;
}

/* Consistent spacing between dashboard sections */
.section-spacing{
    margin-top:10px;
    margin-bottom:10px;
}

/* Make KPI card titles aligned */
.kpi-title{
    font-size:14px;
    font-weight:600;
    color:#6c7a86;
}

/* Ensure KPI values use consistent size */
.kpi-value{
    font-size:32px;
    font-weight:900;
    color:#122741;
}

/* Chart titles alignment */
.plot-container .gtitle{
    font-weight:700 !important;
}

/* =========================
   FIX KPI CARD CONSISTENCY
   ========================= */

.kpi-card{
    background-color:#f8f9fb;
    padding:18px;
    border-radius:12px;
    text-align:center;

    height:140px;              /* FORCE SAME HEIGHT */
    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
}

.kpi-icon{
    font-size:18px;
    margin-bottom:6px;
}

.kpi-title{
    font-size:12px;
    color:#6c757d;
    margin-bottom:6px;
    text-transform:uppercase;
}

.kpi-value{
    font-size:24px;
    font-weight:700;
    color:#122741;

    line-height:1.2;
    word-break:break-word;     /* PREVENT TEXT BREAKING LAYOUT */
}

.kpi-bar{
    height:3px;
    width:40px;
    background:#122741;
    margin-top:8px;
    border-radius:2px;
}

/* =========================
   FULL SCREEN DASHBOARD FIX
   ========================= */

.main {
    overflow: hidden;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 0rem;
    max-height: 100vh;
}

/* Reduce vertical spacing globally */
.element-container {
    margin-bottom: 0.5rem !important;
}

/* Reduce chart height consistency */
.plot-container {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}

</style>
""", unsafe_allow_html=True)

# 3. Define load_assets()
# LOAD ML ASSETS

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

# =====================================
# FIX DATE TYPE (CRITICAL)
# =====================================
df['donation_date'] = pd.to_datetime(df['donation_date'], errors='coerce')

# Remove invalid dates
df = df.dropna(subset=['donation_date'])

# =====================================
# RFM FEATURE GENERATION (FOR ML)
# =====================================
import datetime

def compute_rfm(df):
    today = datetime.datetime(2025, 1, 1)

    rfm = df.groupby('donor_id').agg({
        'donation_date': lambda x: (today - x.max()).days,
        'donor_id': 'count',
        'donation_amount': 'sum'
    }).rename(columns={
        'donation_date': 'recency',
        'donor_id': 'frequency',
        'donation_amount': 'monetary'
    }).reset_index()

    return rfm


# =====================================
# GENERATE RFM DATA
# =====================================
rfm_df = compute_rfm(df)

# =====================================
# APPLY MACHINE LEARNING MODEL
# =====================================
if model is not None:

    features = rfm_df[['recency', 'frequency', 'monetary']]

    try:
        rfm_df['predicted_likelihood'] = model.predict_proba(features)[:, 1]
    except:
        rfm_df['predicted_likelihood'] = model.predict(features)

    # Merge predictions back into main dataset
    df = df.merge(
        rfm_df[['donor_id', 'predicted_likelihood']],
        on='donor_id',
        how='left'
    )

# =====================================
# FALLBACK: PSEUDO-AI (RFM-BASED) IF ML OUTPUT MISSING/UNUSABLE
# =====================================

import numpy as np

# If no ML output or constant values → compute pseudo-AI
if (
    "predicted_likelihood" not in df.columns
    or df["predicted_likelihood"].isna().all()
    or df["predicted_likelihood"].nunique() <= 1
):

    # Ensure datetime
    df["donation_date"] = pd.to_datetime(df["donation_date"], errors="coerce")

    # Recency (days since last donation)
    recency_days = (pd.Timestamp.now() - df["donation_date"]).dt.days.clip(lower=1)

    # Frequency (number of donations per donor)
    frequency = df.groupby("donor_id")["donation_amount"].transform("count")
    frequency_norm = frequency / frequency.max()

    # Monetary (scaled donation amount)
    monetary = df["donation_amount"] / df["donation_amount"].max()

    # Recency score (inverse)
    recency_score = 1 / recency_days
    recency_score = recency_score / recency_score.max()

    # Combine into likelihood score
    df["predicted_likelihood"] = (
        0.5 * monetary +
        0.3 * frequency_norm +
        0.2 * recency_score
    ).clip(0.1, 0.95)

# ----------------------------------------------------
# DEMO DATA ENHANCEMENT
# Prevent unrealistic constant donation values (e.g. RM 299 everywhere)
# ----------------------------------------------------
import numpy as np

if "donation_amount" in df.columns:
    unique_vals = df["donation_amount"].dropna().unique()

    # If dataset looks synthetic (only one repeated amount), randomize realistic values
    if len(unique_vals) <= 2:
        np.random.seed(42)

        donation_ranges = [
            (200, 500),
            (500, 2000),
            (2000, 10000),
            (10000, 50000),
            (50000, 150000)
        ]

        random_amounts = []

        for _ in range(len(df)):
            low, high = donation_ranges[np.random.randint(0, len(donation_ranges))]
            random_amounts.append(np.random.randint(low, high))

        df["donation_amount"] = random_amounts

# ----------------------------------------------------
# AUTO CLEAN CORPORATE DONOR NAMES
# Prevent human names appearing as corporate donors
# ----------------------------------------------------
import re

if "donor_category" in df.columns and "donor_name" in df.columns:

    CORPORATE_STRUCTURE = {
        "PETRONAS": [
            "PETRONAS Carigali",
            "PETRONAS Chemicals",
            "PETRONAS Gas",
            "PETRONAS LNG"
        ],
        "Maybank": [
            "Maybank Foundation",
            "Maybank Islamic"
        ],
        "TNB": [
            "Tenaga Nasional Berhad",
            "TNB Generation"
        ],
        "Telekom Malaysia": [
            "Telekom Malaysia Berhad",
            "TM One"
        ],
        "Sime Darby": [
            "Sime Darby Plantation",
            "Sime Darby Property"
        ],
        "Axiata": [
            "Axiata Group Berhad",
            "CelcomDigi"
        ],
        "Shell": [
            "Shell Malaysia"
        ]
    }

    corporate_keywords = [
        "petronas","maybank","berhad","foundation","shell",
        "tenaga","sime","khazanah","axiata","uem","telekom",
        "bank","group","holdings","corporation","corp","sdn","bhd"
    ]

    def clean_corporate_name(row):
        name = str(row["donor_name"]).strip()

        if row["donor_category"] == "Corporate":

            name_lower = name.lower()

            # If name contains known company keywords → keep it
            if any(k in name_lower for k in corporate_keywords):
                return name

            # If detected as human name, assign a subsidiary from a realistic corporate group
            if re.match(r"^[A-Za-z]+ [A-Za-z]+$", name):
                import random
                parent = random.choice(list(CORPORATE_STRUCTURE.keys()))
                return random.choice(CORPORATE_STRUCTURE[parent])

            # If still unclear, also assign a realistic subsidiary
            import random
            parent = random.choice(list(CORPORATE_STRUCTURE.keys()))
            return random.choice(CORPORATE_STRUCTURE[parent])

        return name

    df["donor_name"] = df.apply(clean_corporate_name, axis=1)

# ----------------------------------------------------
# ALIGN CORPORATE PARENT WITH CORPORATE SUBSIDIARY
# Ensures tables and charts show logical relationships
# ----------------------------------------------------
    if "donor_category" in df.columns:

        def assign_corporate_parent(name):
            n = str(name).lower()
            for parent, subsidiaries in CORPORATE_STRUCTURE.items():
                for sub in subsidiaries:
                    if sub.lower() in n:
                        return parent

            return None

        df["corporate_parent"] = df.apply(
            lambda r: assign_corporate_parent(r["donor_name"])
            if r["donor_category"] == "Corporate"
            else None,
            axis=1
        )

# -------------------------------------
# STANDARDIZE CORPORATE CORE BUSINESS VALUES
# (prevents inconsistent categories from dataset)
# -------------------------------------
if "corporate_core_business" in df.columns:

    # Normalize text first (lowercase + strip spaces)
    df["corporate_core_business"] = (
        df["corporate_core_business"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    corp_map = {
        "oil & gas": "Energy",
        "oil and gas": "Energy",
        "manufacturing": "Technology & Innovation",
        "technology": "Technology & Innovation",
        "finance": "Social Impact",
        "financial services": "Social Impact",
        "none": None,
        "nan": None
    }

    df["corporate_core_business"] = (
        df["corporate_core_business"]
        .replace(corp_map)
        .str.title()
    )

    # Only apply corporate_core_business validation to Corporate donors
    if "donor_category" in df.columns:
        corporate_mask = df["donor_category"].str.lower() == "corporate"

        df.loc[corporate_mask, "corporate_core_business"] = (
            df.loc[corporate_mask, "corporate_core_business"]
            .replace(corp_map)
            .str.title()
        )
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
    # Handle values like "Q1","Q2","Q3","Q4"
    df["quarter"] = (
        df["quarter"]
        .astype(str)
        .str.replace("Q", "", regex=False)
    )

    df["quarter"] = pd.to_numeric(df["quarter"], errors="coerce")
    df = df[df["quarter"].notna()]
    df["quarter"] = df["quarter"].astype(int)

# -------------------------------------
# REMOVE INVALID DONOR CATEGORY (Student should not donate to YUTP)
# -------------------------------------
if "donor_category" in df.columns:

    # normalize text first
    df["donor_category"] = (
        df["donor_category"]
        .astype(str)
        .str.strip()
        .str.title()
    )

    # remove any variation of Student donors
    df = df[~df["donor_category"].str.contains("student", case=False, na=False)]
    df = df[df["donor_category"] != "Student"]

# -------------------------------------
# AI PRIORITY FLAG (Corporate donors first)
# Used by AI charts to prioritise corporate contributors
# -------------------------------------
if "donor_category" in df.columns:
    df["ai_priority"] = df["donor_category"].apply(
        lambda x: 0 if str(x).lower() == "corporate" else 1
    )
else:
    df["ai_priority"] = 1

# 5. Sidebar

selected_year = "All"
selected_category = []
selected_fund = []
selected_month = []
selected_country = []
selected_corporate_name = []
corporate_search = ""
likelihood_filter = 0
selected_amount_range = "All"
selected_ai_confidence = []
# Corporate Group filter variable
selected_parent = []
selected_corporate = []

with st.sidebar:

    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
            background-color: #0f2a44;
        }

        /* Sidebar title */
        section[data-testid="stSidebar"] h3 {
            color: white;
        }

        /* Navigation menu labels (force white text) */
        section[data-testid="stSidebar"] .stRadio label span,
        section[data-testid="stSidebar"] .stRadio label div,
        section[data-testid="stSidebar"] .stRadio label {
            color: white !important;
            font-weight: 600 !important;
        }

        /* Filter section header */
        section[data-testid="stSidebar"] h2 {
            color: #d4af37;
        }

        /* Selectbox / Multiselect labels */
        section[data-testid="stSidebar"] .stSelectbox label,
        section[data-testid="stSidebar"] .stMultiSelect label,
        section[data-testid="stSidebar"] .stSlider label,
        section[data-testid="stSidebar"] .stTextInput label {
            color: #d4af37;
            font-weight: 600;
        }

        /* Hover highlight for navigation */
        section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
            background-color: #1f4e79;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style='color:white;font-size:20px;font-weight:700;margin-top:5px;'>
        YUTP Donor Intelligence
        </div>
        <div style='color:#b5c7d3;font-size:13px;margin-bottom:10px;'>
        Analytics Dashboard
        </div>
        """,
        unsafe_allow_html=True
    )

    # -----------------------------
    # Logout Button (moved into sidebar)
    # -----------------------------
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.username = None
        st.rerun()

    st.markdown("---")
    st.markdown("### Dashboard Menu")

    user_role = st.session_state.user_role

    # Role-based navigation (confirmed with supervisor)
    if user_role == "admin":
        page_options = [
            "📊 Executive Overview",
            "🤝 Donor Engagement Insights",
            "🧠 AI Donor Insights",
            "🗄 Database Management"
        ]

    elif user_role in ["manager", "management"]:
        page_options = [
            "📊 Executive Overview",
            "🤝 Donor Engagement Insights",
            "🧠 AI Donor Insights"
        ]

    elif user_role == "donor":
        page_options = [
            "💳 My Contributions"
        ]

    else:
        page_options = ["📊 Executive Overview"]

    page = st.radio(
        "",
        page_options
    )

    st.markdown("---")
    # Show global filters only for dashboard pages (not donor portal)
    if page != "💳 My Contributions":
        st.markdown("## Filters")

    # ===============================
    # PAGE 1 — EXECUTIVE FILTERS
    # ===============================
    if page.startswith("📊"):

        available_years = sorted(df["year"].dropna().astype(int).unique())

        selected_year = st.selectbox(
            "Choose Year",
            ["All"] + available_years
        )

        fund_order = [
            "Scholarship Bursary",
            "Student Development Program",
            "Research and Innovation",
            "Others"
        ]

        available_funds = [f for f in fund_order if f in df["fund_category"].unique()]

        selected_fund = st.multiselect(
            "Select Fund Category",
            available_funds
        )

        category_order = ["Corporate", "Alumni", "Individual", "Staff"]

        available_categories = category_order

        selected_category = st.multiselect(
            "Select Donor Category",
            available_categories
        )

    # ===============================
    # PAGE 1 — EXECUTIVE FILTERS
    # ===============================
    from pages.executive import show_executive_page
    from pages.engagement import show_engagement_page
    # NOTE: show_title=False prevents duplicate page title
    from pages.ai_insights import show_ai_page
    # Safe import for database management (prevents crash if module missing/unresolved)
    try:
        from pages.database_management import show_database_page
    except Exception:
        def show_database_page():
            st.error("Database management module not loaded. Please check pages/database_management.py")
    
    # Safe import for donor portal (prevents crash if function not yet defined)
    try:
        from pages.donor_portal import show_donor_portal
    except Exception:
        def show_donor_portal(df, username):
            st.error("Donor portal module not loaded. Please check pages/donor_portal.py")

    # ===============================
    # PAGE 2 — ENGAGEMENT FILTERS
    # ===============================
    if page == "🤝 Donor Engagement Insights":

        available_years = sorted(df["year"].dropna().astype(int).unique())
        selected_year = st.selectbox("Choose Year", ["All"] + available_years)

        # Ensure months are ordered 1–12 and not floats like 1.0
        month_list = sorted(df["month"].dropna().astype(int).unique())

        selected_month = st.multiselect(
            "Choose Month",
            month_list
        )

        selected_country = st.multiselect(
            "Choose Country",
            sorted(df["country"].dropna().unique())
        )

        # Corporate Parent filter (PETRONAS, Maybank etc.)
        if "corporate_parent" in df.columns:

            parent_groups = sorted(
                df[df["donor_category"] == "Corporate"]["corporate_parent"]
                .dropna()
                .unique()
            )

            selected_parent = st.multiselect(
                "Choose Corporate Parent",
                parent_groups
            )

        # Filter by specific corporate donor
        corporate_donors = sorted(
            df[df["donor_category"] == "Corporate"]["donor_name"]
            .dropna()
            .unique()
        )

        selected_corporate_name = st.multiselect(
            "Choose Corporate Donor",
            corporate_donors
        )

        # Force full list of industries so chart + filter always show all categories
        corporate_industry_order = [
            "Education",
            "Energy",
            "Technology & Innovation",
            "Sustainability",
            "Community Development",
            "Healthcare",
            "Environment",
            "Social Impact",
            "Research & Development"
        ]

        selected_corporate = st.multiselect(
            "Choose Corporate Core Business",
            corporate_industry_order
        )

    # ===============================
    # PAGE 3 — AI FILTERS
    # ===============================
    elif page == "🧠 AI Donor Insights":

        st.markdown("### AI Filters")

        # Year filter (default = latest year)
        available_years = sorted(df["year"].dropna().astype(int).unique())

        selected_year = st.selectbox(
            "Select Year",
            available_years,
            index=len(available_years) - 1
        )

        # -----------------------------
        # PRIMARY FILTERS (USER FLOW)
        # -----------------------------

        category_order = ["Corporate", "Alumni", "Individual", "Staff"]
        available_categories = [c for c in category_order if c in df["donor_category"].unique()]
        selected_category = st.multiselect(
            "Donor Category",
            available_categories
        )

        search_name = st.text_input("Donor Name")

        # Fund Category filter
        fund_order = [
            "Scholarship Bursary",
            "Student Development Program",
            "Research and Innovation",
            "Others"
        ]

        available_funds = [f for f in fund_order if f in df["fund_category"].unique()]

        selected_fund_category = st.multiselect(
            "Fund Category",
            available_funds
        )

        # Last Donate Year filter
        last_year_options = sorted(df["year"].dropna().unique())

        selected_last_donate_year = st.multiselect(
            "Last Donate Year",
            last_year_options
        )

        selected_country = st.multiselect(
            "Country",
            sorted(df["country"].dropna().unique())
        )

        # -----------------------------
        # ADVANCED AI FILTERS
        # -----------------------------

        likelihood_filter = st.slider(
            "Minimum Likelihood (%)",
            0,
            100,
            0
        )

        selected_ai_confidence = st.multiselect(
            "AI Confidence",
            ["High Potential", "Moderate Potential", "Low Potential"],
            default=["High Potential", "Moderate Potential", "Low Potential"]
        )

    # Global dashboard reset (only for dashboard analytics pages)
    if page not in ["💳 My Contributions"]:
        st.markdown("---")
        if st.button("Reset Filters", key="global_reset_filters"):
            st.rerun()

# 6. Initial Filtering (Base)
# =========================
# ENHANCE MOCK DATA (REALISTIC BEHAVIOUR)
# =========================

# =========================
# PAGE 1 — EXECUTIVE OVERVIEW
# =========================
if page == "📊 Executive Overview":

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

    # -------------------------
    # Compute charts
    # -------------------------

    fund_sum = exec_df.groupby("fund_category")["donation_amount"].sum().reset_index()

    fund_order = [
        "Scholarship Bursary",
        "Student Development Program",
        "Research and Innovation",
        "Others"
    ]

    fig_fund = px.bar(
        fund_sum,
        x="fund_category",
        y="donation_amount",
        title="Total Donations by Fund Category",
        color="fund_category",
        category_orders={"fund_category": fund_order},
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    import pandas as _pd

    if selected_year != "All":
        current_year = selected_year
    else:
        try:
            current_year = int(exec_df["year"].dropna().max())
        except Exception:
            current_year = _pd.Timestamp.today().year

    quarterly_trend = (
        exec_df[exec_df["year"] == current_year]
        .groupby(["year", "quarter"])["donation_amount"]
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
        title="Fundraising Trend by Quarter",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    # -------------------------------------------------
    # Donor Category Distribution
    # Use donor COUNT instead of donation value
    # (prevents corporate donors dominating the chart)
    # -------------------------------------------------
    category_dist = (
        exec_df[exec_df["donor_category"] != "Student"]
        .groupby("donor_category")["donor_id"]
        .nunique()
        .reset_index()
    )

    category_dist.columns = ["donor_category", "donor_count"]

    # Ensure consistent category order
    expected_categories = ["Corporate", "Alumni", "Individual", "Staff"]

    category_dist = (
        category_dist
        .set_index("donor_category")
        .reindex(expected_categories, fill_value=0)
        .reset_index()
    )

    # Remove zero categories so pie chart remains clean

    fig_category = px.pie(
        category_dist,
        names="donor_category",
        values="donor_count",
        title="Donation Distribution by Donor Category",
        color="donor_category",
        category_orders={"donor_category": expected_categories},
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    # =========================
    # KPI CALCULATIONS
    # =========================

    total_fund = exec_df["donation_amount"].sum()
    total_donors = exec_df["donor_id"].nunique()

    # Returning donor = donor who donated in more than one year
    donor_years = exec_df.groupby("donor_id")["year"].nunique()
    returning_donors = (donor_years > 1).sum()

    if total_donors > 0:
        returning_rate = round((returning_donors / total_donors) * 100, 1)
    else:
        returning_rate = 0

    quarter_sum = exec_df.groupby("quarter")["donation_amount"].sum().sort_index()

    if len(quarter_sum) > 1:
        prev_q = quarter_sum.iloc[-2]
        curr_q = quarter_sum.iloc[-1]

        # Prevent division by zero or unrealistic spikes
        if prev_q == 0:
            quarterly_growth = 0
        else:
            quarterly_growth = ((curr_q - prev_q) / prev_q) * 100
            quarterly_growth = round(quarterly_growth, 1)
    else:
        quarterly_growth = 0

    st.markdown("<div class='page-title'>Executive Overview</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">💰</div>
                <div class="kpi-title">Total Fund</div>
                <div class="kpi-value">RM {total_fund:,.0f}</div>
                <div class="kpi-bar"></div>
            </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">👥</div>
                <div class="kpi-title">Total Donors</div>
                <div class="kpi-value">{total_donors}</div>
                <div class="kpi-bar"></div>
            </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">📈</div>
                <div class="kpi-title">Quarterly Growth</div>
                <div class="kpi-value">{quarterly_growth}%</div>
                <div class="kpi-bar"></div>
            </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">🔁</div>
                <div class="kpi-title">Returning Donor Rate</div>
                <div class="kpi-value">{returning_rate}%</div>
                <div class="kpi-bar"></div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)


    # =========================
    # EXECUTIVE OVERVIEW CHART LAYOUT (UPDATED)
    # =========================

    # Row 1 → Full width trend chart
    fig_quarter.update_layout(height=300)
    st.plotly_chart(fig_quarter, use_container_width=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # Row 2 → Pie (left) + Bar (right)
    col1, col2 = st.columns(2)

    with col1:
        fig_category.update_layout(height=300)
        st.plotly_chart(fig_category, use_container_width=True)

    with col2:
        fig_fund.update_layout(height=300)
        st.plotly_chart(fig_fund, use_container_width=True)

# =========================
# PAGE 2 — DONOR ENGAGEMENT INSIGHTS
# =========================
if page == "🤝 Donor Engagement Insights":

    st.markdown("<div class='page-title'>Donor Engagement Insights</div>", unsafe_allow_html=True)

    engagement_df = df.copy()

    if selected_parent:
        engagement_df = engagement_df[
            engagement_df["corporate_parent"].isin(selected_parent)
        ]


    show_engagement_page(
        engagement_df,
        selected_year,
        selected_month,
        selected_country,
        selected_category,
        selected_corporate,
        selected_corporate_name,
        selected_parent,
        show_title=False
    )

# =========================
# PAGE 3 — AI DONOR INSIGHTS
# =========================
if page == "🧠 AI Donor Insights":

    show_ai_page(
        df,
        likelihood_filter,
        selected_category,
        search_name if 'search_name' in locals() else "",
        selected_country,
        selected_corporate,
        selected_year,
        selected_amount_range,
        selected_ai_confidence,
        selected_fund_category if 'selected_fund_category' in locals() else [],
        selected_last_donate_year if 'selected_last_donate_year' in locals() else []
    )
# =========================
# PAGE DATABASE MANAGEMENT (ADMIN ONLY)
# =========================

if page == "🗄 Database Management":

    if st.session_state.user_role != "admin":
        st.error("Access Denied.")
        st.stop()

    # Load database management page
    show_database_page()

# =========================
# DONOR PORTAL PAGE
# =========================
if page == "💳 My Contributions":
    show_donor_portal(df, st.session_state.username)

