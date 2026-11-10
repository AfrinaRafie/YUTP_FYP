import streamlit as st
import pandas as pd
import plotly.express as px


def show_executive_page(df, selected_year, selected_fund, selected_category):

    st.write("EXECUTIVE PAGE LOADED")   # 👈 ADD HERE

    st.markdown("## Executive Overview")

    exec_df = df.copy()

    if selected_year != "All":
        exec_df = exec_df[exec_df["year"] == selected_year]

    if selected_fund:
        exec_df = exec_df[exec_df["fund_category"].isin(selected_fund)]

    if selected_category:
        exec_df = exec_df[exec_df["donor_category"].isin(selected_category)]

    # -------------------------
    # Fund category chart
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

    fig_fund.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title_font_size=14
    )

    # -------------------------
    # Quarterly trend
    # -------------------------

    if selected_year != "All":
        current_year = selected_year
    else:
        current_year = exec_df["year"].max()

    quarterly_trend = (
        exec_df[exec_df["year"] == current_year]
        .groupby(["year", "quarter"])["donation_amount"]
        .sum()
        .reset_index()
    )

    quarterly_trend["Year_Quarter"] = (
        quarterly_trend["year"].astype(str) +
        " Q" +
        quarterly_trend["quarter"].astype(str)
    )

    fig_quarter = px.line(
        quarterly_trend,
        x="Year_Quarter",
        y="donation_amount",
        markers=True,
        title="Fundraising Trend by Quarter",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig_quarter.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title_font_size=14
    )

    # -------------------------
    # Donor category pie
    # -------------------------

    category_dist = (
        exec_df.groupby("donor_category")["donation_amount"]
        .sum()
        .reset_index()
    )

    fig_category = px.pie(
        category_dist,
        names="donor_category",
        values="donation_amount",
        title="Donation Distribution by Donor Category",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    # -------------------------
    # KPI calculations
    # -------------------------

    total_fund = exec_df["donation_amount"].sum()
    total_donors = exec_df["donor_id"].nunique()

    donor_counts = exec_df.groupby("donor_id").size()
    returning_donors = (donor_counts > 1).sum()

    if total_donors > 0:
        returning_rate = round((returning_donors / total_donors) * 100, 1)
    else:
        returning_rate = 0

    quarter_sum = exec_df.groupby("quarter")["donation_amount"].sum().sort_index()

    if len(quarter_sum) > 1:
        quarterly_growth = ((quarter_sum.iloc[-1] - quarter_sum.iloc[-2]) / quarter_sum.iloc[-2]) * 100
        quarterly_growth = round(quarterly_growth, 1)
    else:
        quarterly_growth = 0

    # -------------------------
    # KPI ROW
    # -------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Total Fund", f"RM {total_fund:,.0f}")

    with c2:
        st.metric("Total Donors", total_donors)

    with c3:
        st.metric("Quarterly Growth", f"{quarterly_growth}%")

    with c4:
        st.metric("Returning Donor Rate", f"{returning_rate}%")

    # =========================
    # AI INSIGHT (FINAL CLEAN VERSION)
    # =========================

    if exec_df.empty:
        insight_lines = ["No data available to generate insights."]
    else:
        # Top fund category
        if not fund_sum.empty:
            top_fund_row = fund_sum.sort_values("donation_amount", ascending=False).iloc[0]
            top_fund = top_fund_row["fund_category"]
            top_fund_amt = top_fund_row["donation_amount"]
        else:
            top_fund = "N/A"
            top_fund_amt = 0

        # Top donor category
        if not category_dist.empty:
            top_cat_row = category_dist.sort_values("donation_amount", ascending=False).iloc[0]
            top_cat = top_cat_row["donor_category"]
            top_cat_amt = top_cat_row["donation_amount"]
        else:
            top_cat = "N/A"
            top_cat_amt = 0

        insight_lines = [
            f"Total funds raised: RM {total_fund:,.0f}",
            f"Top fund category: {top_fund} (RM {top_fund_amt:,.0f})",
            f"Top donor category: {top_cat} (RM {top_cat_amt:,.0f})",
            f"Quarterly growth: {quarterly_growth}%",
            f"Returning donor rate: {returning_rate}%"
        ]

    # DISPLAY (VERY CLEAR)
    st.markdown("## 🧠 AI Executive Insight")

    for line in insight_lines:
        st.markdown(f"- {line}")

    st.markdown("<div style='height:25px'></div>", unsafe_allow_html=True)
    # -------------------------
    # Charts layout
    # -------------------------

    with st.container(border=True):
        st.plotly_chart(fig_quarter, use_container_width=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2, border=True)

    with col1:
        st.plotly_chart(fig_category, use_container_width=True)

    with col2:
        st.plotly_chart(fig_fund, use_container_width=True)