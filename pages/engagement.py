import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np


def show_engagement_page(
    df,
    selected_year,
    selected_month,
    selected_country,
    selected_category,
    selected_corporate,
    selected_corporate_name,
    selected_parent,
    show_title=True
):
    # Apply corporate parent filter only if the column exists
    if selected_parent and "corporate_parent" in df.columns:
        df = df[df["corporate_parent"].isin(selected_parent)]

    if show_title:
        st.markdown("<div class='page-title'>Donor Engagement Insights</div>", unsafe_allow_html=True)
    
    


    # =========================
    # APPLY FILTERS
    # =========================

    # Corporate subsidiary will always be the donor_name
    corp_name_col = "donor_name"

    eng_df = df.copy()

    # Ensure event_name column exists and replace placeholder values
    event_map = {
        1: "UTP Annual Dinner",
        2: "UTP Innovation Challenge",
        3: "Sustainability Summit",
        4: "Scholarship & Bursary Ceremony",
        5: "YUTP Charity Golf",
        6: "Student Development Fundraiser",
        7: "Research & Innovation Showcase"
    }

    if "event_name" not in eng_df.columns:
        if "Event_Name" in eng_df.columns:
            eng_df = eng_df.rename(columns={"Event_Name": "event_name"})
        elif "campaign_id" in eng_df.columns:
            eng_df["event_name"] = eng_df["campaign_id"].map(event_map)
        else:
            eng_df["event_name"] = None

    # Replace generic placeholders like "General Donation"
    eng_df["event_name"] = eng_df["event_name"].replace(
        ["General Donation", "General Fundraising", None],
        np.nan
    )

    if "campaign_id" in eng_df.columns:
        eng_df["event_name"] = eng_df["event_name"].fillna(
            eng_df["campaign_id"].map(event_map)
        )

    # If still missing, assign events based on month (more realistic for reporting)
    remaining_mask = eng_df["event_name"].isna()
    if remaining_mask.any() and "month" in eng_df.columns:

        def map_event_by_month(m):
            if m in [1, 2]:
                return "UTP Annual Dinner"
            elif m in [3, 4]:
                return "UTP Innovation Challenge"
            elif m in [5, 6]:
                return "Sustainability Summit"
            elif m in [7, 8]:
                return "Scholarship & Bursary Ceremony"
            elif m in [9, 10]:
                return "YUTP Charity Golf"
            else:
                return "Research & Innovation Showcase"

        eng_df.loc[remaining_mask, "event_name"] = eng_df.loc[remaining_mask, "month"].apply(map_event_by_month)

    if selected_corporate_name:
        eng_df = eng_df[
            eng_df["donor_name"].isin(selected_corporate_name)
        ]

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

    # =========================
    # MONTHLY TREND
    # =========================

    monthly_trend = (
        eng_df.groupby(["year", "month"])["donation_amount"]
        .sum()
        .reset_index()
        .sort_values(["year", "month"])
    )

    monthly_trend["Date"] = pd.to_datetime(
        monthly_trend["year"].astype(str) + "-"
        + monthly_trend["month"].astype(str) + "-01"
    )

    fig_monthly = px.line(
        monthly_trend,
        x="Date",
        y="donation_amount",
        markers=True,
        title=None,
        color=None,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_monthly.update_layout(
        height=280,
        xaxis_title=None,
        yaxis_title=None,
        legend_title=None,
        showlegend=False
    )
    fig_monthly.update_layout(title_font=dict(size=14))
    fig_monthly.update_layout(title_x=0)
    fig_monthly.update_traces(name="")
    fig_monthly.for_each_annotation(lambda a: a.update(text=""))
    fig_monthly.update_layout(annotations=[])
    for trace in fig_monthly.data:
        trace.name = None

    # =========================
    # ALUMNI MAP
    # =========================

    alumni_country = (
        eng_df[(eng_df["donor_category"] == "Alumni") & (eng_df["country"].notna())]
        .groupby("country")["donation_amount"]
        .sum()
        .reset_index()
    )

    fig_alumni_map = px.choropleth(
        alumni_country,
        locations="country",
        locationmode="country names",
        color="donation_amount",
        hover_name="country",
        title=None,
        color_continuous_scale="Blues"
    )

    fig_alumni_map.update_layout(
        height=320,
        geo=dict(
            showland=True,
            landcolor="lightgrey",
            projection_scale=1.2,
            center=dict(lat=3, lon=101)
        )
    )
    fig_alumni_map.update_layout(coloraxis_colorbar_title=None)
    fig_alumni_map.update_coloraxes(colorbar_title=None)
    fig_alumni_map.for_each_annotation(lambda a: a.update(text=""))
    fig_alumni_map.update_layout(annotations=[])

    # Auto zoom when single country selected
    if selected_country and len(selected_country) == 1:
        fig_alumni_map.update_layout(
            geo=dict(projection_scale=3)
        )

    # =========================
    # CORPORATE INDUSTRY
    # =========================

    corp_df = eng_df[eng_df["donor_category"] == "Corporate"]

    # Ensure corporate_parent column exists but DO NOT overwrite it with donor names
    corp_df = corp_df.copy()

    if "corporate_parent" not in corp_df.columns:
        corp_df["corporate_parent"] = None

    # Only keep rows where corporate_parent exists for corporate analysis
    corp_df = corp_df[corp_df["corporate_parent"].notna()]

    # Clean data to prevent 'undefined' labels in charts
    corp_df = corp_df.dropna(subset=["corporate_core_business", "corporate_parent"])
    corp_df = corp_df[
        corp_df["corporate_core_business"].astype(str).str.strip() != ""
    ]
    corp_df["corporate_core_business"] = corp_df["corporate_core_business"].astype(str)
    corp_df["corporate_parent"] = corp_df["corporate_parent"].astype(str)

    corp_name_col = "corporate_parent"

    # Ensure event_name exists and clean placeholder values
    if "event_name" not in corp_df.columns:
        if "Event_Name" in corp_df.columns:
            corp_df = corp_df.rename(columns={"Event_Name": "event_name"})
        elif "campaign_id" in corp_df.columns:
            corp_df["event_name"] = corp_df["campaign_id"].map(event_map)
        else:
            corp_df["event_name"] = None

    corp_df["event_name"] = corp_df["event_name"].replace(
        ["General Donation", "General Fundraising", None],
        np.nan
    )

    if "campaign_id" in corp_df.columns:
        corp_df["event_name"] = corp_df["event_name"].fillna(
            corp_df["campaign_id"].map(event_map)
        )

    remaining_mask = corp_df["event_name"].isna()
    if remaining_mask.any() and "month" in corp_df.columns:

        def map_event_by_month(m):
            if m in [1, 2]:
                return "UTP Annual Dinner"
            elif m in [3, 4]:
                return "UTP Innovation Challenge"
            elif m in [5, 6]:
                return "Sustainability Summit"
            elif m in [7, 8]:
                return "Scholarship & Bursary Ceremony"
            elif m in [9, 10]:
                return "YUTP Charity Golf"
            else:
                return "Research & Innovation Showcase"

        corp_df.loc[remaining_mask, "event_name"] = corp_df.loc[remaining_mask, "month"].apply(map_event_by_month)

    # Calculate total contribution per industry
    corp_breakdown = (
        corp_df.groupby("corporate_core_business")["donation_amount"]
        .sum()
        .reset_index()
    )

    corp_order = [
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

    corp_breakdown = (
        corp_breakdown
        .set_index("corporate_core_business")
        .reindex(corp_order, fill_value=0)
        .reset_index()
    )

    fig_corp = px.bar(
        corp_breakdown,
        y="corporate_core_business",
        x="donation_amount",
        title=None,
        category_orders={"corporate_core_business": corp_order},
        orientation="h",
        color="corporate_core_business",
        color_discrete_sequence=[
            "#0f2a44",
            "#122741",
            "#1f4e79",
            "#2f6fed",
            "#4a7fb0",
            "#6c9bcf",
            "#8fb8e0",
            "#a9c9eb",
            "#c6dcf5"
        ]
    )

    fig_corp.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        legend_title=None,
        showlegend=False
    )
    fig_corp.update_layout(height=280)
    fig_corp.update_layout(title_font=dict(size=14))

    fig_corp.update_layout(title_x=0)
    fig_corp.update_traces(name="")
    fig_corp.for_each_annotation(lambda a: a.update(text=""))
    fig_corp.update_layout(annotations=[])
    for trace in fig_corp.data:
        trace.name = None

    # =========================
    # CORPORATE CONTRIBUTION LEADERBOARD
    # =========================

    corp_summary = (
        corp_df.groupby("corporate_parent", as_index=False)
        .agg(
            Total_Donation=("donation_amount", "sum"),
            Events_Sponsored=("event_name", "nunique"),
            Sample_Event=("event_name", "first")
        )
        .sort_values("Total_Donation", ascending=False)
    )

    fig_corp_leaderboard = px.bar(
        corp_summary.head(10),
        y="corporate_parent",
        x="Total_Donation",
        title=None,
        color="Total_Donation",
        color_continuous_scale="Tealgrn",
        orientation="h",
        hover_data={
            "Events_Sponsored": True,
            "Sample_Event": True
        }
    )

    fig_corp_leaderboard.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        legend_title=None,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title_font_size=14,
        showlegend=False
    )
    fig_corp_leaderboard.update_layout(height=280)
    fig_corp_leaderboard.update_layout(title_font=dict(size=14))

    fig_corp_leaderboard.update_layout(title_x=0)
    fig_corp_leaderboard.update_layout(coloraxis_colorbar_title=None)
    fig_corp_leaderboard.update_coloraxes(colorbar_title=None)
    fig_corp_leaderboard.update_traces(name="")
    fig_corp_leaderboard.for_each_annotation(lambda a: a.update(text=""))
    fig_corp_leaderboard.update_layout(annotations=[])
    for trace in fig_corp_leaderboard.data:
        trace.name = None

    fig_corp_leaderboard.update_traces(
        hovertemplate="<b>%{y}</b><br>Total Donation: RM %{x:,.0f}<br>Events Sponsored: %{customdata[0]}<br>Example Event: %{customdata[1]}"
    )

    # =========================
    # CORPORATE TABLE
    # =========================

    corporate_events = (
        corp_df
        .groupby([corp_name_col, "donor_name", "event_name", "year"])["donation_amount"]
        .sum()
        .reset_index()
        .sort_values("donation_amount", ascending=False)
    )

    corporate_events.rename(columns={
        corp_name_col: "Corporate Parent",
        "donor_name": "Corporate Subsidiary",
        "event_name": "Event",
        "year": "Year",
        "donation_amount": "Total Donation (RM)"
    }, inplace=True)

    # =========================
    # POWER BI STYLE GRID LAYOUT
    # =========================

    # ROW 1
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### Monthly Fundraising Trend")
            st.plotly_chart(fig_monthly, use_container_width=True)

    with col2:
        with st.container(border=True):
            st.markdown("### Global Alumni Donations by Country")
            st.plotly_chart(fig_alumni_map, use_container_width=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ROW 2
    col3, col4 = st.columns(2)

    with col3:
        with st.container(border=True):
            st.markdown("### Corporate Donations by Impact Sector")
            st.plotly_chart(fig_corp, use_container_width=True)

    with col4:
        with st.container(border=True):
            st.markdown("### Top Corporate Contributors")
            st.plotly_chart(fig_corp_leaderboard, use_container_width=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ROW 3 (TABLE - allow minimal scroll)
    with st.container(border=True):
        st.markdown("### Corporate Contribution Details")
        st.dataframe(
            corporate_events,
            use_container_width=True,
            height=300
        )