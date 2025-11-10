import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fusion Proofing Assignment Tool", layout="wide")

st.title("Fusion Proofing Assignment Tool")

# Load shared Google Sheet as data source
sheet_url = "https://docs.google.com/spreadsheets/d/1n1LFx5NLqVKNjpJysrai_M3PX-KuinHZUaZEMX7sBac/export?format=xlsx"

try:
    # Read all sheets from the Google Sheet
    all_sheets = pd.read_excel(sheet_url, sheet_name=None)
    data = all_sheets[list(all_sheets.keys())[0]]  # first sheet for assignment rules
    deliverables_df = all_sheets.get("Sheet3")  # third sheet for deliverables

    st.success("Fusion rule data loaded from shared source.")

    # Clean column names
    data.columns = data.columns.str.strip().str.lower().str.replace(" ", "_")

    def extract_unique_values(column):
        if column not in data.columns:
            return []
        split_values = data[column].dropna().astype(str).str.split(',')
        flat_list = [item.strip() for sublist in split_values for item in sublist]
        return sorted(set(flat_list))

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Request Details")
        st.text_input("Subject")
        st.text_input("Customer Contact")
        st.text_area("Briefly Describe your Request", height=150)
        st.text_area("Please include relevant sources", height=100)
        st.selectbox("Related to another project?", ["Yes", "No"])

        st.subheader("Asset Info")
        countries = st.multiselect("Countries who will use this asset?", options=extract_unique_values('country'))
        asset_type = st.selectbox("Asset Type", options=[""] + extract_unique_values('project_type'))
        categories = st.multiselect("Brand Names in Scope", options=extract_unique_values('category'))

        st.selectbox("Department", ["Marketing", "Creative", "Regulatory", "Sales", "Operations", "Other"])
        st.selectbox("Priority Rating", ["High", "Medium", "Low"])
        st.date_input("Proof must be completed by")
        st.text_input("Completion date reason")

        st.subheader("Deliverable Types (based on Asset Type selection)")
        if deliverables_df is not None:
            deliverables_df.columns = deliverables_df.columns.str.strip().str.lower().str.replace(" ", "_")
            deliverables_df['asset_type'] = deliverables_df['asset_type'].fillna(method='ffill')
            matching_rows = deliverables_df[deliverables_df['asset_type'].str.lower() == asset_type.lower()] if asset_type else pd.DataFrame()
            deliverables = matching_rows['deliverable_type'].dropna().tolist()
            if deliverables:
                for d in deliverables:
                    st.markdown(f"- {d}")
            else:
                st.write("No deliverables defined for this asset type.")
        else:
            st.info("Deliverables sheet not found.")

        st.subheader("User Assignment Review")
        selected_user = st.selectbox("Select a specific user to view their criteria:", [""] + sorted(data['name'].dropna().unique().tolist()))

    def matches(row):
        def field_blocks(row_val, selected_vals):
            if pd.isna(row_val) or str(row_val).strip() == '':
                return False
            if not selected_vals:
                return True
            rule_values = set(x.strip().lower() for x in str(row_val).split(',') if x.strip())
            selected_values = set(x.lower() for x in selected_vals)
            return not rule_values.intersection(selected_values)

        if field_blocks(row.get('country', ''), countries):
            return False
        if field_blocks(row.get('category', ''), categories):
            return False
        if asset_type and field_blocks(row.get('project_type', ''), [asset_type]):
            return False
        return True

    filtered = data[data.apply(matches, axis=1)]

    team_order = ['WIP', 'Content', 'Messaging', 'Management', 'Executive', 'Production']

    def extract_sort_key(team_val):
        for level in team_order:
            if level.lower() in str(team_val).lower():
                return team_order.index(level)
        return len(team_order)

    if not filtered.empty:
        filtered = filtered.sort_values(by='team', key=lambda col: col.map(extract_sort_key))

    with col2:
        st.subheader(f"Matching Assignments ({len(filtered)} found)")
        if not filtered.empty:
            st.dataframe(
                filtered[['name', 'team']].drop_duplicates().reset_index(drop=True),
                use_container_width=True,
                height=600
            )
        else:
            st.warning("No matching assignments found.")

    with col1:
        if selected_user:
            st.markdown("---")
            st.subheader(f"Criteria for {selected_user}")
            user_row = data[data['name'].str.lower() == selected_user.lower()]
            if not user_row.empty:
                user_info = user_row.iloc[0]
                st.markdown(f"**Countries who will use this asset?:** {user_info.get('country', '—')}")
                st.markdown(f"**Brand Names in Scope:** {user_info.get('category', '—')}")
                st.markdown(f"**Asset Type:** {user_info.get('project_type', '—')}")
                st.markdown(f"**Team:** {user_info.get('team', '—')}")
            else:
                st.warning("User not found.")

except Exception as e:
    st.error(f"Failed to load data: {e}")
