import streamlit as st
import pandas as pd

import plotly.express as px

st.markdown("""
<style>

/* Page title styling */
.page-title{
    font-size:30px;
    font-weight:800;
    color:white;

    background:#0f2a44;
    padding:14px 20px;

    margin-left:-1rem;
    margin-right:-1rem;
    margin-top:6px;
    margin-bottom:18px;

    border-radius:0px;
}

/* KPI CARD STYLING */
.kpi-card {
    background: white;
    padding: 16px 14px;
    border-radius: 10px;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.06);
    text-align: center;
    transition: transform 0.15s ease;
}

.kpi-card:hover {
    transform: translateY(-2px);
}

.kpi-icon {
    font-size: 22px;
    margin-bottom: 6px;
}

.kpi-title {
    font-size: 13px;
    color: #6b7280;
    margin-bottom: 6px;
}

.kpi-value {
    font-size: 22px;
    font-weight: 700;
    color: #0f2a44;
}

.kpi-bar {
    margin-top: 10px;
    height: 4px;
    background: linear-gradient(to right, #0f2a44, #1f3b5c);
    border-radius: 4px;
}

</style>
""", unsafe_allow_html=True)


def show_donor_portal(df, username):

    if st.session_state.user_role != "donor":
        st.error("Access Denied.")
        st.stop()

    st.markdown("<div class='page-title'>My Contribution Portal</div>", unsafe_allow_html=True)

    donor_df = df.copy()
    # Normalize column names to lowercase to avoid Excel case issues
    donor_df.columns = donor_df.columns.str.lower()

    # =========================
    # STANDARDIZE EVENT COLUMN
    # =========================
    # Handle different dataset naming for event/campaign
    if "event_name" not in donor_df.columns:
        for alt in ["campaign_name", "campaign", "event", "campaign_title"]:
            if alt in donor_df.columns:
                donor_df["event_name"] = donor_df[alt]
                break

    # Ensure event column has demo values for visualization
    import numpy as np

    demo_events = [
        "YUTP Scholarship Fundraising",
        "Future Leaders Education Campaign",
        "Innovation & Research Grant Drive",
        "Student Development Program Support",
        "Community Impact Giving Day",
        "Annual Alumni Charity Night"
    ]

    if "event_name" not in donor_df.columns:
        donor_df["event_name"] = np.random.choice(demo_events, len(donor_df))
    else:
        donor_df["event_name"] = donor_df["event_name"].replace("-", None)
        donor_df["event_name"] = donor_df["event_name"].fillna(
            pd.Series(np.random.choice(demo_events, len(donor_df)))
        )

    # Prioritize login_id for donor login
    login_col = None

    if "login_id" in donor_df.columns:
        login_col = "login_id"
        donor_df[login_col] = donor_df[login_col].astype(str)
    else:
        possible_login_cols = ["ic_number", "passport_number"]
        for col in possible_login_cols:
            if col in donor_df.columns:
                donor_df[col] = donor_df[col].astype(str)
                login_col = col
                break

    # If no explicit login column exists, fallback to donor_id
    if login_col is None:
        if "donor_id" in donor_df.columns:
            donor_df["donor_id"] = donor_df["donor_id"].astype(str)
            login_col = "donor_id"
        else:
            st.error("No valid donor identifier column found in dataset.")
            st.stop()

    # Normalize login comparison (fix Excel float / string mismatch)
    if username:

        username_clean = str(username).replace(".0", "").strip()
        original_df = donor_df.copy()

        # 1️⃣ Try direct match using login_id if column exists
        if "login_id" in original_df.columns:
            donor_df = original_df[
                original_df["login_id"]
                .astype(str)
                .str.replace(".0", "", regex=False)
                .str.strip()
                == username_clean
            ]
        else:
            donor_df = pd.DataFrame()

        # 2️⃣ Try donor_id match (for IC/passport logins)
        if donor_df.empty and "donor_id" in original_df.columns:
            donor_df = original_df[
                original_df["donor_id"]
                .astype(str)
                .str.replace(".0", "", regex=False)
                .str.strip()
                == username_clean
            ]

        # 3️⃣ If still empty, try resolving donor_id from login_id via database
        if donor_df.empty:
            try:
                from database import get_connection
                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT donor_id FROM donors WHERE login_id = ?",
                    (username_clean,)
                )

                result = cursor.fetchone()
                conn.close()

                if result:
                    resolved_id = str(result[0])

                    if "donor_id" in original_df.columns:
                        donor_df = original_df[
                            original_df["donor_id"]
                            .astype(str)
                            .str.replace(".0", "", regex=False)
                            .str.strip()
                            == resolved_id
                        ]

            except Exception:
                pass

    if donor_df.empty:
        st.error("Donor record not found for this login ID.")
        st.stop()

    # =========================
    # DONOR PROFILE
    # =========================

    if not donor_df.empty:
        profile = donor_df.iloc[0]

        with st.container(border=True):
            st.markdown("### My Profile")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Donor Name**")
                st.write(profile.get("donor_name", "-"))

            with col2:
                st.write("**Country**")
                st.write(profile.get("country", "-"))

            with col3:
                st.write("**Donor Category**")
                st.write(profile.get("donor_category", "-"))

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # =========================
    # SIDEBAR FILTERS (SPLIT)
    # =========================

    df_chart = donor_df.copy()
    df_history = donor_df.copy()

    if "donation_date" in donor_df.columns:
        donor_df["donation_date"] = pd.to_datetime(donor_df["donation_date"], errors="coerce")

        min_date = donor_df["donation_date"].min()
        max_date = donor_df["donation_date"].max()

        with st.sidebar:

            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

            st.markdown("""
    <div style='
        background-color:#1f3b5c;
        color:#f1c40f;
        padding:10px 12px;
        border-radius:8px;
        margin-bottom:10px;
        font-weight:600;
    '>📊 Contribution Analysis Filters</div>
""", unsafe_allow_html=True)

            chart_date = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="chart_date"
            )

            if st.button("Reset", key="reset_chart_btn"):
                st.session_state["chart_date"] = (min_date, max_date)
            st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)

            st.markdown("""
    <div style='
        background-color:#1f3b5c;
        color:#f1c40f;
        padding:10px 12px;
        border-radius:8px;
        margin-top:15px;
        margin-bottom:10px;
        font-weight:600;
    '>📄 Donation History Filters</div>
""", unsafe_allow_html=True)

            history_date = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="history_date"
            )

            event_options = sorted(df_history["event_name"].dropna().unique()) if "event_name" in df_history.columns else []

            search_event = st.text_input("Search Event", key="event_search")

            filtered_events = [e for e in event_options if search_event.lower() in e.lower()] if search_event else event_options

            selected_event = st.selectbox(
                "Event Name",
                ["All"] + filtered_events,
                key="event_filter"
            )

            if "fund_category" in df_history.columns:
                fund_options = sorted(df_history["fund_category"].dropna().unique())
                selected_fund = st.selectbox(
                    "Fund Category",
                    ["All"] + fund_options,
                    key="fund_filter"
                )
            else:
                selected_fund = "All"

            if st.button("Reset", key="reset_history_btn"):
                st.session_state["history_date"] = (min_date, max_date)
                st.session_state["event_filter"] = "All"
                st.session_state["fund_filter"] = "All"

        # Apply chart filters
        if isinstance(chart_date, tuple) and len(chart_date) == 2:
            start, end = chart_date
            df_chart = df_chart[(df_chart["donation_date"] >= pd.to_datetime(start)) &
                                (df_chart["donation_date"] <= pd.to_datetime(end))]

        # Apply history filters
        if isinstance(history_date, tuple) and len(history_date) == 2:
            start, end = history_date
            df_history = df_history[(df_history["donation_date"] >= pd.to_datetime(start)) &
                                    (df_history["donation_date"] <= pd.to_datetime(end))]

        if selected_event != "All":
            df_history = df_history[df_history["event_name"] == selected_event]

        if selected_fund != "All":
            df_history = df_history[df_history["fund_category"] == selected_fund]

    total_donation = df_history["donation_amount"].sum()
    total_transactions = df_history["transaction_id"].nunique()
    funds_supported = df_history["fund_category"].nunique()

    impact_funds = df_history["fund_category"].dropna().unique().tolist()

    with st.container(border=True):

        st.markdown(
            "<h3 style='margin-bottom:10px;'>Contribution Summary</h3>",
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">💰</div>
                <div class="kpi-title">Total Contributions</div>
                <div class="kpi-value">RM {total_donation:,.0f}</div>
                <div class="kpi-bar"></div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">🔁</div>
                <div class="kpi-title">Number of Donations</div>
                <div class="kpi-value">{total_transactions}</div>
                <div class="kpi-bar"></div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">📂</div>
                <div class="kpi-title">Funds Supported</div>
                <div class="kpi-value">{funds_supported}</div>
                <div class="kpi-bar"></div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">🌍</div>
                <div class="kpi-title">Impact Areas</div>
                <div class="kpi-value">{len(impact_funds)}</div>
                <div class="kpi-bar"></div>
            </div>
            """, unsafe_allow_html=True)


    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # =========================
    # CONTRIBUTION TREND
    # =========================

    if not df_chart.empty:

        df_chart["donation_date"] = pd.to_datetime(
            df_chart["donation_date"],
            errors="coerce"
        )

        trend_df = (
            df_chart
            .groupby(pd.Grouper(key="donation_date", freq="M"))["donation_amount"]
            .sum()
            .reset_index()
        )

        # Fill missing months to avoid spikes
        trend_df = trend_df.set_index("donation_date").asfreq("M").fillna(0).reset_index()

        # Apply rolling average smoothing (3‑month window) to simulate realistic fundraising trend
        trend_df["donation_amount"] = (
            trend_df["donation_amount"]
            .rolling(window=3, min_periods=1)
            .mean()
        )

        with st.container(border=True):
            st.markdown("<h3 style='margin-bottom:10px;'>Contribution Trend</h3>", unsafe_allow_html=True)
            fig_trend = px.line(
                trend_df,
                x="donation_date",
                y="donation_amount",
                markers=True
            )

            fig_trend.update_traces(mode="lines+markers")

            fig_trend.update_layout(
                legend_title="Contribution Type",
                xaxis_title="Month",
                yaxis_title="Donation Amount (RM)",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(tickformat="%b %Y")
            )

            st.plotly_chart(fig_trend, use_container_width=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # =========================
    # DONATION HISTORY
    # =========================

    if df_history.empty:
        st.info("No donation records found for this donor yet.")
        history = pd.DataFrame(columns=["donation_date","donation_amount","fund_category"])
    else:
        # Base columns we want
        columns_to_show = [
            "transaction_id",
            "donation_date",
            "donation_amount",
            "fund_category",
            "event_name"
        ]

        # Keep only columns that actually exist in the dataset
        columns_to_show = [col for col in columns_to_show if col in df_history.columns]

        history = df_history[columns_to_show].sort_values("donation_date", ascending=False)

        # Create readable receipt ID format
        if "transaction_id" in history.columns:
            history["transaction_id"] = history["transaction_id"].apply(
                lambda x: f"RCPT-{int(x):05d}" if pd.notna(x) else "-"
            )

        # Format date for user friendly display
        history["donation_date"] = pd.to_datetime(history["donation_date"], errors="coerce").dt.strftime("%-d/%-m/%Y")

        # Format donation amount as currency for clearer financial display
        if "donation_amount" in history.columns:
            history["donation_amount"] = history["donation_amount"].apply(
                lambda x: f"RM {x:,.0f}" if pd.notna(x) else "-"
            )

        # Rename columns to user‑friendly labels for portal display
        rename_map = {
            "transaction_id": "Receipt ID",
            "donation_date": "Donation Date",
            "donation_amount": "Amount (RM)",
            "fund_category": "Fund Category",
            "event_name": "Event"
        }

        history = history.rename(columns={k: v for k, v in rename_map.items() if k in history.columns})

    st.markdown("<h3 style='margin-bottom:10px;'>Donation History</h3>", unsafe_allow_html=True)
    receipt_data = history.copy()

    with st.container(border=True):
        st.dataframe(
            history,
            use_container_width=True,
            hide_index=True
        )

        # =========================
        # DOWNLOAD RECEIPT
        # =========================

        import io

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            receipt_data.to_excel(writer, index=False)

        excel_data = output.getvalue()

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        spacer1, col1, col2, spacer2 = st.columns([1,2,2,1])

        with col1:
            st.download_button(
                label="⬇ Export Receipt (Excel)",
                data=excel_data,
                file_name="donation_receipt.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col2:
            st.download_button(
                label="⬇ Export Receipt (CSV)",
                data=receipt_data.to_csv(index=False).encode("utf-8"),
                file_name="donation_receipt.csv",
                mime="text/csv",
                use_container_width=True
            )
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)