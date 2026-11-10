import streamlit as st

def load_css():
    st.markdown("""
    <style>

    .main {
        background-color: #ffffff;
    }

    /* Sidebar Section Containers */
    .sidebar-section {
        background-color: #f3f9f8;
        padding: 12px;
        border-radius: 10px;
        border-left: 5px solid #326b71;
        margin-bottom: 12px;
    }

    /* Dashboard Row Container */
    .dashboard-row {
        background-color: #ffffff;
        padding: 22px;
        border-radius: 18px;
        border: 1px solid #edf2f7;
        box-shadow: 0 10px 28px rgba(18,39,65,0.08);
        margin-bottom: 18px;
        transition: all 0.2s ease;
    }

    .dashboard-row:hover {
        box-shadow: 0 14px 36px rgba(18,39,65,0.12);
    }

    /* Chart Container */
    .chart-box {
        background-color: #ffffff;
        padding: 18px;
        border-radius: 16px;
        border: 1px solid #edf2f7;
        box-shadow: 0 8px 24px rgba(18,39,65,0.07);
        transition: all 0.2s ease;
    }

    .chart-box:hover {
        box-shadow: 0 12px 30px rgba(18,39,65,0.10);
    }

    /* KPI Cards Wrapper Row */
    .kpi-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 18px;
    }

    /* KPI Cards - aligned size and modern style */
    .kpi-card {
        background: linear-gradient(135deg, #ffffff 0%, #f4f8ff 100%);
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #e6eef7;
        box-shadow: 0 10px 26px rgba(18,39,65,0.10);
        text-align: center;

        min-height: 125px;
        width: 100%;
        height: 100%;

        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        gap: 6px;

        transition: all 0.25s ease;
    }

    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 16px 34px rgba(18,39,65,0.14);
    }

    .kpi-title {
        font-size: 12px;
        color: #2f6fed;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
        opacity: 0.9;
    }

    /* KPI Icon */
    .kpi-icon {
        font-size: 22px;
        margin-bottom: 4px;
        color: #2f6fed;
    }

    .kpi-value {
        font-size: 28px;
        color: #122741; /* dark blue */
        font-weight: 900;
        line-height: 1.2;
        letter-spacing: 0.5px;
        margin-top: 2px;
        text-align: center;
        word-break: break-word;
        max-width: 100%;
    }

    /* KPI Trend Indicator (▲ ▼) */
    .kpi-trend {
        font-size: 14px;
        font-weight: 700;
        margin-top: 6px;
    }

    .kpi-trend.up {
        color: #2e7d32;  /* green for positive growth */
    }

    .kpi-trend.down {
        color: #c62828;  /* red for negative growth */
    }

    /* Small indicator bar under KPI */
    .kpi-bar {
        height: 7px;
        border-radius: 4px;
        margin-top: 10px;
        background: linear-gradient(90deg, #2f6fed, #122741);
    }

    /* Optional sparkline container (tiny trend chart placeholder) */
    .kpi-sparkline {
        margin-top: 8px;
        height: 35px;
    }

    /* Page Titles (Executive + Engagement Pages) */
    .page-title {
        font-size: 34px;
        font-weight: 800;
        color: #122741;
        margin-bottom: 10px;
    }

    .page-subtitle {
        font-size: 15px;
        color: #c9a227;
        font-weight: 600;
        margin-bottom: 25px;
    }

    /* AI Section */
    .ai-container {
        background-color: #fcfcfc;
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #80ae9a;
        margin: auto;
    }

    /* AI Insight Summary Card */
    .ai-summary-card {
        background: linear-gradient(135deg, #122741 0%, #2f6fed 100%);
        padding: 18px;
        border-radius: 14px;
        margin-bottom: 20px;
        color: white;
        box-shadow: 0 8px 22px rgba(18,39,65,0.15);
        font-size: 14px;
        line-height: 1.6;
    }

    .ai-summary-title {
        font-size: 16px;
        font-weight: 800;
        margin-bottom: 6px;
    }

    /* Filter Boxes */
    .filter-box {
        background-color: #f5f9f8;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #326b71;
        margin-bottom: 12px;
    }

    .sidebar .stSelectbox,
    .sidebar .stMultiSelect,
    .sidebar .stTextInput {
        margin-bottom: 10px;
    }

    .filter-title {
        font-weight: 700;
        color: #122741;
        margin-bottom: 5px;
        font-size: 14px;
    }

    /* LOGIN PAGE */

    .login-container {
        background-color: #ffffff;
        padding: 28px;
        border-radius: 18px;
        border: 1px solid #e6eef7;
        box-shadow: 0 12px 32px rgba(18,39,65,0.12);
        max-width: 420px;
        margin: 120px auto 0 auto; /* vertically center-ish */
    }

    .login-container .stButton button {
        width: 100%;
        background-color: #122741;
        color: white;
        font-weight: 700;
        border-radius: 8px;
        padding: 10px;
        border: none;
    }

    .login-container .stButton button:hover {
        background-color: #2f6fed;
    }

    </style>
    """, unsafe_allow_html=True)