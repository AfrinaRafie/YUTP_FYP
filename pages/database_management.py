import streamlit as st
import sqlite3
import pandas as pd

with st.sidebar:
    st.markdown("""
        <div style="
            background-color: white;
            padding: 12px 0;
            text-align: center;
            border-bottom: 1px solid #e5e7eb;
        ">
    """, unsafe_allow_html=True)

    st.image("YUTPlogo.jpg", width=140)

    st.markdown("</div>", unsafe_allow_html=True)

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

</style>
""", unsafe_allow_html=True)


def show_database_page():

    st.markdown("<div class='page-title'>Database Management</div>", unsafe_allow_html=True)

    # =========================
    # SIDEBAR LOGO
    # =========================
    with st.sidebar:
        st.markdown("""
            <div style="
                background-color: white;
                padding: 15px 0;
                margin-top: -20px;
                margin-left: -10px;
                margin-right: -10px;
                text-align: center;
                border-bottom: 1px solid #e5e7eb;
            ">
        """, unsafe_allow_html=True)

        st.image("YUTPlogo.jpg", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    DB_PATH = "yutp_donor_system.db"  # changeable for deployment
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # =========================
    # ADD NEW DONOR
    # =========================

    st.markdown("### Add New Donor")

    with st.form("add_donor_form"):

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Donor Name")
            category = st.selectbox(
                "Donor Category",
                ["Corporate", "Individual", "Alumni", "Staff"]
            )

        with col2:
            country = st.text_input("Country")
            sector = st.selectbox(
                "Corporate Core Business",
                [
                    "Energy",
                    "Technology & Innovation",
                    "Education",
                    "Healthcare",
                    "Environment",
                    "Social Impact"
                ]
            )

        submit = st.form_submit_button("Add Donor")

        if submit:

            if name.strip() == "" or country.strip() == "":
                st.warning("Please fill in all required fields (Name & Country)")
            else:
                # Basic duplicate check
                existing = cursor.execute(
                    "SELECT * FROM donors WHERE donor_name = ? AND country = ?",
                    (name, country)
                ).fetchone()

                if existing:
                    st.warning("This donor already exists.")
                    st.stop()

                cursor.execute("""
                    INSERT INTO donors (
                        donor_name,
                        donor_category,
                        country,
                        corporate_core_business
                    )
                    VALUES (?, ?, ?, ?)
                """, (name, category, country, sector))

                conn.commit()

                st.success("Donor added successfully")
                st.rerun()

    st.divider()


    # =========================
    # SMART UPLOAD DATASET (FOR YUTP STAFF)
    # =========================

    st.markdown("### Upload Donor Dataset")

    uploaded_file = st.file_uploader(
        "Upload Excel File (.xlsx)",
        type=["xlsx"],
        key="smart_upload"
    )

    if uploaded_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_file)
            valid_sheets = []
            skipped_sheets = []

            required_columns = ["donor_name", "donor_category", "country"]

            for sheet in xls.sheet_names:
                df_sheet = pd.read_excel(xls, sheet_name=sheet)

                # Standardize column names for checking
                df_sheet.columns = (
                    df_sheet.columns
                    .str.strip()
                    .str.lower()
                    .str.replace(" ", "_")
                )

                # Temporary mapping for detection
                column_mapping = {
                    "donor name": "donor_name",
                    "name": "donor_name",
                    "donor": "donor_name",
                    "category": "donor_category",
                    "donor category": "donor_category",
                    "country name": "country",
                    "nation": "country",
                    "sector": "corporate_core_business",
                    "business": "corporate_core_business"
                }

                df_sheet.rename(columns=column_mapping, inplace=True)

                # Check if sheet contains required donor fields
                if all(col in df_sheet.columns for col in required_columns):
                    valid_sheets.append(df_sheet)
                else:
                    skipped_sheets.append(sheet)

            if not valid_sheets:
                st.error("No valid sheets found with required donor structure.")
                st.stop()

            upload_df = pd.concat(valid_sheets, ignore_index=True)

            # Show info to user
            st.info(f"Loaded {len(valid_sheets)} valid sheet(s). Skipped: {skipped_sheets}")

            # -------------------------
            # STANDARDIZE COLUMN NAMES
            # -------------------------
            upload_df.columns = (
                upload_df.columns
                .str.strip()
                .str.lower()
                .str.replace(" ", "_")
            )

            # Column mapping (handles messy real data)
            column_mapping = {
                "donor name": "donor_name",
                "name": "donor_name",
                "donor": "donor_name",
                "category": "donor_category",
                "donor category": "donor_category",
                "country name": "country",
                "nation": "country",
                "sector": "corporate_core_business",
                "business": "corporate_core_business"
            }

            upload_df.rename(columns=column_mapping, inplace=True)

            st.write("Preview of cleaned data:")
            st.dataframe(upload_df.head(), use_container_width=True)

            if st.button("Import to Database"):

                required_columns = ["donor_name", "donor_category", "country"]

                missing_cols = [col for col in required_columns if col not in upload_df.columns]

                if missing_cols:
                    st.error(f"Missing required columns: {missing_cols}")
                    st.stop()

                inserted = 0
                skipped = 0

                for _, row in upload_df.iterrows():

                    name = str(row.get("donor_name", "")).strip()
                    country = str(row.get("country", "")).strip()

                    if name == "" or country == "":
                        skipped += 1
                        continue

                    # Duplicate check
                    existing = cursor.execute(
                        "SELECT * FROM donors WHERE donor_name = ? AND country = ?",
                        (name, country)
                    ).fetchone()

                    if existing:
                        skipped += 1
                        continue

                    cursor.execute("""
                        INSERT INTO donors (
                            donor_name,
                            donor_category,
                            country,
                            corporate_core_business
                        )
                        VALUES (?, ?, ?, ?)
                    """, (
                        name,
                        row.get("donor_category"),
                        country,
                        row.get("corporate_core_business", "")
                    ))

                    inserted += 1

                conn.commit()

                st.success(f"Import completed: {inserted} inserted, {skipped} skipped (duplicates/invalid)")

                st.rerun()

        except Exception as e:
            st.error(f"Error processing file: {e}")

    st.divider()

    # =========================
    # VIEW DONOR RECORDS
    # =========================

    st.markdown("### Donor Records")
    st.markdown("", unsafe_allow_html=True)
    st.markdown("""
<style>

/* Donor table container */
.donor-container {
    background-color: #ffffff;
    padding: 18px;
    border-radius: 10px;
    border: 1px solid #e5e7eb;
    margin-top: 10px;
}

/* Table header */
.donor-header {
    font-weight: 600;
    color: #111827;
    padding: 10px 0;
    border-bottom: 2px solid #e5e7eb;
}

/* Table rows */
.donor-row {
    padding: 8px 0;
    border-bottom: 1px solid #f1f5f9;
}

/* Alternating row colors */
.donor-row:nth-child(even) {
    background-color: #f9fafb;
}

/* Hover highlight */
.donor-row:hover {
    background-color: #eef2ff;
}

/* Edit button */
button[kind="secondary"] {
    border-radius: 6px;
}

</style>
""", unsafe_allow_html=True)

    # Search donor by name
    search_query = st.text_input("Search Donor Name")

    # Pagination settings and rows per page selection
    rows_per_page = st.selectbox("Rows per page", [10, 20, 50], index=1)
    page = st.number_input("Page", min_value=1, value=1, step=1)
    offset = (page - 1) * rows_per_page

    # Load only required rows
    query = f"SELECT * FROM donors LIMIT {rows_per_page} OFFSET {offset}"
    donors = pd.read_sql_query(query, conn)

    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        selected_category = st.selectbox(
            "Filter by Donor Category",
            ["All", "Corporate", "Individual", "Alumni", "Staff"]
        )

    with filter_col2:
        countries = ["All"] + sorted(donors["country"].dropna().unique().tolist()) if 'donors' in locals() else ["All"]
        selected_country = st.selectbox(
            "Filter by Country",
            countries
        )

    if search_query:
        donors = donors[donors["donor_name"].str.contains(search_query, case=False, na=False)]

    if selected_category != "All":
        donors = donors[donors["donor_category"] == selected_category]

    if selected_country != "All":
        donors = donors[donors["country"] == selected_country]

    st.caption(f"Showing {len(donors)} records (Page {page})")

    if donors.empty:
        st.info("No donor records found.")
    else:
        with st.container(border=True):
            st.markdown("### Donor Records")

            # Column headers
            header1, header2, header3, header4, header5, header6 = st.columns([3,2,2,2,1,1])
            header1.markdown("**Donor Name**")
            header2.markdown("**Category**")
            header3.markdown("**Country**")
            header4.markdown("**Core Business**")
            header5.markdown("**Edit**")
            header6.markdown("**Delete**")

            # Rows
            for index, row in donors.iterrows():
                col1, col2, col3, col4, col5, col6 = st.columns([3,2,2,2,1,1])

                col1.write(row["donor_name"])
                col2.write(row["donor_category"])
                col3.write(row["country"])
                col4.write(row.get("corporate_core_business", "-"))

                if col5.button("Edit", key=f"edit_{row['donor_id']}"):
                    st.session_state.edit_donor = row["donor_id"]

                if col6.button("Delete", key=f"delete_{row['donor_id']}"):
                    st.session_state.confirm_delete = row["donor_id"]

        # Confirmation dialog
        if "confirm_delete" in st.session_state:

            delete_id = st.session_state.confirm_delete

            st.warning("Are you sure you want to delete this donor?")

            confirm_col1, confirm_col2 = st.columns(2)

            with confirm_col1:
                if st.button("Confirm Delete"):
                    cursor.execute(
                        "DELETE FROM donors WHERE donor_id = ?",
                        (delete_id,)
                    )
                    conn.commit()

                    del st.session_state.confirm_delete

                    st.success("Donor deleted successfully")
                    st.rerun()

            with confirm_col2:
                if st.button("Cancel"):
                    del st.session_state.confirm_delete
                    st.rerun()


    # Export donors
    if not donors.empty:
        csv_donors = donors.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Export Donors to CSV",
            data=csv_donors,
            file_name="yutp_donors_export.csv",
            mime="text/csv"
        )

    st.divider()

    # =========================
    # EDIT DONOR
    # =========================

    if "edit_donor" in st.session_state:

        donor_id = st.session_state.edit_donor

        donor_data = pd.read_sql_query(
            "SELECT * FROM donors WHERE donor_id = ?",
            conn,
            params=(donor_id,)
        ).iloc[0]

        st.markdown("### Edit Donor Information")

        with st.form("edit_donor_form"):

            new_name = st.text_input("Donor Name", donor_data["donor_name"])

            category_options = ["Corporate", "Individual", "Alumni", "Staff"]
            # Safe index handling
            if donor_data["donor_category"] in category_options:
                default_index = category_options.index(donor_data["donor_category"])
            else:
                default_index = 0  # fallback

            new_category = st.selectbox(
                "Donor Category",
                category_options,
                index=default_index
            )

            new_country = st.text_input("Country", donor_data["country"])

            new_sector = st.text_input(
                "Corporate Core Business",
                donor_data.get("corporate_core_business", "")
            )

            update_submit = st.form_submit_button("Update Donor")

            if update_submit:
                # Normalize category before update
                new_category = new_category.strip().title()

                cursor.execute(
                    """
                    UPDATE donors
                    SET donor_name=?, donor_category=?, country=?, corporate_core_business=?
                    WHERE donor_id=?
                    """,
                    (new_name, new_category, new_country, new_sector, donor_id)
                )

                conn.commit()

                del st.session_state.edit_donor

                st.success("Donor updated successfully")
                st.rerun()

    st.divider()

    # =========================
    # VIEW DONATION RECORDS
    # =========================

    st.markdown("### Donation Records")

    try:
        donations = pd.read_sql_query("SELECT * FROM donations", conn)
    except:
        st.warning("No 'donations' table found in database.")
        donations = pd.DataFrame()

    if donations.empty:
        st.info("No donation records found.")
    else:
        st.dataframe(donations, use_container_width=True)

        # Export donations
        csv_donations = donations.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Export Donations to CSV",
            data=csv_donations,
            file_name="yutp_donations_export.csv",
            mime="text/csv"
        )

    # Debug info (safe for production visibility)
    st.caption(f"Connected to DB: {DB_PATH}")

    conn.close()