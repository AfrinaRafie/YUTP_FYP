import streamlit as st
import pandas as pd
import plotly.express as px



def show_ai_page(
    df,
    likelihood_filter,
    selected_category,
    search_name,
    selected_country,
    selected_corporate,
    selected_year,
    selected_amount_range,
    selected_ai_confidence,
    selected_fund_category,
    selected_last_donate_year
):

    # SAFETY CHECK
    if "predicted_likelihood" not in df.columns:
        df["predicted_likelihood"] = 0.5

    st.markdown("<div class='page-title'>AI Donor Insights</div>", unsafe_allow_html=True)

    # =========================
    # Aggregate per donor
    # =========================

    # Ensure donation_date is datetime BEFORE aggregation
    df["donation_date"] = pd.to_datetime(df["donation_date"], errors="coerce")

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
            "fund_category": "last"
        })
        .reset_index()
    )

    # Add last donation year + formatted date
    donor_summary["last_donate_year"] = pd.to_datetime(donor_summary["donation_date"]).dt.year
    donor_summary["last_donate_date"] = pd.to_datetime(donor_summary["donation_date"]).dt.strftime("%d/%m/%y")

    donor_summary["fund_category"] = donor_summary[
        "fund_category"
    ].fillna("General Donation")

    donor_summary["Likelihood (%)"] = (
        donor_summary["predicted_likelihood"] * 100
    ).round(1)

    # Dynamic threshold (top 30% donors)
    threshold = donor_summary["Likelihood (%)"].quantile(0.7)

    # DEBUG / DISPLAY
    # st.write(f"Dynamic threshold: {threshold:.1f}%")

    # AI Confidence classification (robust + guaranteed distribution)
    try:
        donor_summary["AI Confidence"] = pd.qcut(
            donor_summary["Likelihood (%)"],
            q=[0, 0.3, 0.6, 1.0],
            labels=["Low Potential", "Moderate Potential", "High Potential"],
            duplicates="drop"
        )
    except Exception:
        donor_summary["AI Confidence"] = "Moderate Potential"

    # Ensure ALL categories exist (force balanced demo distribution if needed)
    categories = donor_summary["AI Confidence"].unique()

    if len(categories) < 3:
        donor_summary = donor_summary.sort_values("Likelihood (%)")

        n = len(donor_summary)
        low_cut = int(n * 0.3)
        mod_cut = int(n * 0.6)

        donor_summary.loc[donor_summary.index[:low_cut], "AI Confidence"] = "Low Potential"
        donor_summary.loc[donor_summary.index[low_cut:mod_cut], "AI Confidence"] = "Moderate Potential"
        donor_summary.loc[donor_summary.index[mod_cut:], "AI Confidence"] = "High Potential"

    # =========================
    # KPI SUMMARY
    # =========================

    high_potential = donor_summary[donor_summary["Likelihood (%)"] >= threshold].shape[0]

    predicted_total = (
        donor_summary["donation_amount"] *
        (1 + donor_summary["predicted_likelihood"])
    ).sum()

    top_donor = (
        donor_summary.sort_values("predicted_likelihood", ascending=False)
        .iloc[0]["donor_name"]
        if not donor_summary.empty else "N/A"
    )

    top_category = (
        donor_summary["fund_category"].mode()[0]
        if not donor_summary.empty else "N/A"
    )

    spacer1, c1, c3, c4, spacer2 = st.columns([1, 2, 2, 2, 1])

    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">High Potential Donors</div>
            <div class="kpi-value">{high_potential}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Top Target Donor</div>
            <div class="kpi-value">{top_donor}</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Most Promising Fund</div>
            <div class="kpi-value">{top_category}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:25px'></div>", unsafe_allow_html=True)

    # =========================
    # Apply filters
    # =========================

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

    if selected_category:
        donor_summary = donor_summary[
            donor_summary["donor_category"].isin(selected_category)
        ]

    if selected_fund_category:
        donor_summary = donor_summary[
            donor_summary["fund_category"].isin(selected_fund_category)
        ]
    
    # Last Donate Year filter
    if selected_last_donate_year:
        donor_summary = donor_summary[
            donor_summary["last_donate_year"].isin(selected_last_donate_year)
        ]

    # Apply AI Confidence filter FIRST
    if selected_ai_confidence:
        donor_summary = donor_summary[
            donor_summary["AI Confidence"].isin(selected_ai_confidence)
        ]
    # Apply likelihood filter ONLY if no specific AI confidence selected
    elif likelihood_filter > 0:
        donor_summary = donor_summary[
            donor_summary["Likelihood (%)"] >= likelihood_filter
        ]

    # =========================
    # AI TABLE
    # =========================

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    with st.container(border=True):

        table_df = donor_summary.copy()

        # Ensure AI Confidence is string (important for mapping)
        table_df["AI Confidence"] = table_df["AI Confidence"].astype(str)

        # Define correct order
        confidence_order = {
            "High Potential": 0,
            "Moderate Potential": 1,
            "Low Potential": 2
        }

        table_df["confidence_order"] = table_df["AI Confidence"].map(confidence_order)

        table_df = table_df.sort_values(
            ["confidence_order", "Likelihood (%)"],
            ascending=[True, False]
        ).drop(columns=["confidence_order"])

        table_df["Contact"] = (
            table_df["donor_name"].str.replace(" ", ".").str.lower()
            + "@example.com"
        )

        def format_confidence(x):
            if x == "High Potential":
                return "🟢 High Potential"
            elif x == "Moderate Potential":
                return "🟡 Moderate Potential"
            else:
                return "🔴 Low Potential"

        table_df["AI Confidence"] = table_df["AI Confidence"].apply(format_confidence)

        table_df.rename(columns={"fund_category": "Fund Category"}, inplace=True)

        st.markdown("### Donor Contribution Likelihood")

        display_df = table_df[[
            "donor_name",
            "donor_category",
            "country",
            "corporate_core_business",
            "Likelihood (%)",
            "last_donate_year",
            "AI Confidence",
            "Fund Category",
            "Contact"
        ]]

        st.dataframe(display_df, use_container_width=True, height=350)

    # =========================
    # STRATEGIC RECOMMENDATION
    # =========================

    if search_name and not donor_summary.empty:
        top_target = donor_summary.sort_values(
            "predicted_likelihood", ascending=False
        ).iloc[0]

        likelihood_pct = round(top_target["predicted_likelihood"] * 100, 1)

        # Enhanced dynamic recommendation (multi-factor logic)
        donation_amt = top_target["donation_amount"]
        category = top_target["donor_category"]
        fund = top_target["fund_category"]

        if likelihood_pct >= 70:
            if donation_amt > donor_summary["donation_amount"].mean():
                recommendation = f"Invite this donor for the upcoming {fund} event and prepare a personalised proposal highlighting impact and recognition opportunities."
            else:
                recommendation = f"Include this donor in targeted outreach for the upcoming {fund} campaign and maintain engagement through personalised communication."

        elif likelihood_pct >= 40:
            if category == "Corporate":
                recommendation = f"Engage this corporate donor for potential collaboration or sponsorship in the upcoming {fund} initiative."
            else:
                recommendation = f"Nurture this donor through personalised updates and invite them to participate in upcoming {fund} programmes."

        else:
            if donation_amt < donor_summary["donation_amount"].mean():
                recommendation = "Re-engage this donor through awareness campaigns, event invitations, or follow-up communication to rebuild interest."
            else:
                recommendation = "Reconnect with this previously active donor through personalised appreciation and targeted engagement strategies."

        with st.container(border=True):
            st.markdown("### Strategic Fundraising Recommendation")

            # Build explanation (WHY this donor has this likelihood)
            avg_amount = donor_summary["donation_amount"].mean()

            # Calculate additional metrics
            total_amount = round(donation_amt, 2)
            donor_freq = df[df["donor_id"] == top_target["donor_id"]].shape[0]

            # Percentile ranking (Monetary)
            temp_summary = donor_summary.copy()
            temp_summary["amount_percentile"] = temp_summary["donation_amount"].rank(pct=True)

            donor_percentile = temp_summary.loc[
                temp_summary["donor_id"] == top_target["donor_id"],
                "amount_percentile"
            ].values[0] * 100

            avg_freq = df.groupby("donor_id")["donation_amount"].count().mean()

            explanation = []

            if donation_amt > avg_amount:
                explanation.append("Higher-than-average contribution value")
            else:
                explanation.append("Lower-than-average contribution value")

            if likelihood_pct >= 70:
                explanation.append("Strong historical engagement pattern")
            elif likelihood_pct >= 40:
                explanation.append("Moderate engagement behaviour")
            else:
                explanation.append("Limited or declining engagement")

            last_year = top_target["last_donate_year"] if pd.notna(top_target["last_donate_year"]) else "N/A"
            explanation.append(f"Most recent donation recorded in {last_year}")

            explanation.append(f"Total contribution: RM {total_amount:,.0f} (Top {100 - donor_percentile:.0f}% donor segment)")

            if donor_freq > avg_freq:
                explanation.append(f"Donation frequency: {donor_freq} times (above average engagement)")
            else:
                explanation.append(f"Donation frequency: {donor_freq} times (below average engagement)")

            explanation_text = "\n".join([f"• {item}" for item in explanation])

            st.success(
                f"""
Strategic Fundraising Insight

Selected Donor
**{top_target['donor_name']}**

Estimated Likelihood to Contribute Again
**{likelihood_pct}%**

Last Donation Date
**{top_target['last_donate_date']}**

Suggested Event
**{fund} Fundraising Campaign**

Why this donor?
{explanation_text}

Recommended Action
{recommendation}
"""
            )
    else:
        with st.container(border=True):
            st.markdown("### Strategic Fundraising Recommendation")
            st.info("Select a donor using the search filter to view AI-based recommendation.")

    st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)


    # =========================
    # DONATION PREDICTION CHART
    # =========================

    pred_chart_df = donor_summary.copy()

    pred_chart_df["Predicted Next Donation"] = (
        pred_chart_df["donation_amount"] * (1 + pred_chart_df["predicted_likelihood"])
    )


    chart_df = pred_chart_df[[
        "donor_name",
        "donation_amount",
        "Predicted Next Donation"
    ]].copy()

    chart_df = chart_df.sort_values("Predicted Next Donation", ascending=False).head(10)

    chart_df = chart_df.melt(
        id_vars=["donor_name"],
        value_vars=["donation_amount", "Predicted Next Donation"],
        var_name="Type",
        value_name="Amount"
    )

    chart_df["Type"] = chart_df["Type"].replace({
        "donation_amount": "Previous Donation",
        "Predicted Next Donation": "Predicted Donation"
    })

    fig_prediction = px.bar(
        chart_df,
        x="donor_name",
        y="Amount",
        color="Type",
        title="",
        barmode="group"
    )

    fig_prediction.update_layout(
        height=280,
        xaxis_title="Donor",
        yaxis_title="Donation Amount (RM)"
    )

    # =========================
    # MONTHLY ENGAGEMENT PREDICTION
    # =========================

    # donor_summary["donation_date"] = pd.to_datetime(donor_summary["donation_date"], errors="coerce")

    donor_summary["year"] = donor_summary["donation_date"].dt.year

    if selected_year != "All":
        donor_summary = donor_summary[donor_summary["year"] == selected_year]
        
    high_df = donor_summary[donor_summary["Likelihood (%)"] >= threshold].copy()
    if high_df.empty:
        high_df = donor_summary.copy()

    high_df["months_to_next"] = (
        (1 - high_df["predicted_likelihood"]) * 6
    ).round().astype(int)

    high_df["Predicted Next Donation Date"] = (
        high_df["donation_date"] + pd.to_timedelta(high_df["months_to_next"] * 30, unit="D")
    )

    high_df["Predicted Month"] = high_df["Predicted Next Donation Date"].dt.to_period("M").astype(str)

    monthly_high = (
        high_df.groupby("Predicted Month")
        .size()
        .reset_index(name="Predicted High-Potential Donors")
    )

    fig_high = px.bar(
        monthly_high,
        x="Predicted Month",
        y="Predicted High-Potential Donors",
        title=""
    )
    fig_high.update_layout(height=280)

    # =========================
    # POWER BI STYLE CHART GRID
    # =========================

    with st.container(border=True):
        st.markdown("### Estimated Future Donations from Existing Donors")
        st.plotly_chart(fig_prediction, use_container_width=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("### Predicted Donor Engagement Opportunities")
        st.plotly_chart(fig_high, use_container_width=True)
