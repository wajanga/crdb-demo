import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt

# Initialize session state for dynamic data
if "atm_data" not in st.session_state:
    st.session_state.atm_data = pd.DataFrame(columns=["REFERENCE", "DEBIT", "CREDIT", "CURRENCY"])
if "cbs_data" not in st.session_state:
    st.session_state.cbs_data = pd.DataFrame(columns=["REFERENCE", "DEBIT", "CREDIT", "CURRENCY"])

# Function to generate default data
def generate_fake_data():
    atm_data = pd.DataFrame([
        {"REFERENCE": "1001", "DEBIT": 100000, "CREDIT": 0, "CURRENCY": "TZS"},
        {"REFERENCE": "1002", "DEBIT": 50000, "CREDIT": 0, "CURRENCY": "TZS"},
        {"REFERENCE": "1003", "DEBIT": 200000, "CREDIT": 0, "CURRENCY": "TZS"},
        {"REFERENCE": "1004", "DEBIT": 75000, "CREDIT": 0, "CURRENCY": "TZS"},
    ])

    cbs_data = pd.DataFrame([
        {"REFERENCE": "1001", "DEBIT": 100000, "CREDIT": 0, "CURRENCY": "TZS"},
        {"REFERENCE": "1002", "DEBIT": 45000, "CREDIT": 0, "CURRENCY": "TZS"},  # Mismatch
        {"REFERENCE": "1004", "DEBIT": 75000, "CREDIT": 0, "CURRENCY": "TZS"},
        {"REFERENCE": "1005", "DEBIT": 30000, "CREDIT": 0, "CURRENCY": "TZS"},  # Extra in CBS
    ])
    
    return atm_data, cbs_data

# Load Fake Data Initially
if st.sidebar.button("Load Fake Data"):
    atm_data, cbs_data = generate_fake_data()
    st.session_state.atm_data = atm_data
    st.session_state.cbs_data = cbs_data
    st.success("Fake Data Loaded!")

# Function to reconcile data
def reconcile_data(atm_data, cbs_data):
    discrepancies = []

    # Merge data on REFERENCE
    merged_data = pd.merge(atm_data, cbs_data, on="REFERENCE", how="outer", suffixes=("_ATM", "_CBS"), indicator=True)

    for _, row in merged_data.iterrows():
        if row["_merge"] == "left_only":
            discrepancies.append({"REFERENCE": row["REFERENCE"], "Issue": "Missing in CBS"})
        elif row["_merge"] == "right_only":
            discrepancies.append({"REFERENCE": row["REFERENCE"], "Issue": "Missing in ATM"})
        elif row["DEBIT_ATM"] != row["DEBIT_CBS"]:
            discrepancies.append({"REFERENCE": row["REFERENCE"], "Issue": "Amount Mismatch"})

    return pd.DataFrame(discrepancies)

# Function to generate Excel file
def generate_excel_report(discrepancy_df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        discrepancy_df.to_excel(writer, index=False, sheet_name="Discrepancies")
    return output.getvalue()

# Streamlit UI
st.title("🏦 ATM vs CBS Reconciliation App")

# File Upload Section
st.sidebar.header("📂 Upload Files")
atm_file = st.sidebar.file_uploader("Upload ATM Log (Excel)", type=["xlsx"])
cbs_file = st.sidebar.file_uploader("Upload CBS Report (Excel)", type=["xlsx"])

# Process Uploaded Files
if atm_file:
    st.session_state.atm_data = pd.read_excel(atm_file)
if cbs_file:
    st.session_state.cbs_data = pd.read_excel(cbs_file)

# Display Data Entry Section
st.sidebar.header("➕ Add Transaction Data")

# Add New ATM Transaction
with st.sidebar.form("Add ATM Transaction"):
    reference = st.text_input("Transaction Reference (ATM)")
    debit = st.number_input("Debit Amount", min_value=0.0, step=1000.0)
    credit = st.number_input("Credit Amount", min_value=0.0, step=1000.0)
    currency = st.text_input("Currency", value="TZS")

    if st.form_submit_button("Add to ATM"):
        new_atm_entry = pd.DataFrame([{"REFERENCE": reference, "DEBIT": debit, "CREDIT": credit, "CURRENCY": currency}])
        st.session_state.atm_data = pd.concat([st.session_state.atm_data, new_atm_entry], ignore_index=True)
        st.success(f"ATM Transaction {reference} added!")

# Add New CBS Transaction
with st.sidebar.form("Add CBS Transaction"):
    reference_cbs = st.text_input("Transaction Reference (CBS)")
    debit_cbs = st.number_input("Debit Amount (CBS)", min_value=0.0, step=1000.0)
    credit_cbs = st.number_input("Credit Amount (CBS)", min_value=0.0, step=1000.0)
    currency_cbs = st.text_input("Currency (CBS)", value="TZS")

    if st.form_submit_button("Add to CBS"):
        new_cbs_entry = pd.DataFrame([{"REFERENCE": reference_cbs, "DEBIT": debit_cbs, "CREDIT": credit_cbs, "CURRENCY": currency_cbs}])
        st.session_state.cbs_data = pd.concat([st.session_state.cbs_data, new_cbs_entry], ignore_index=True)
        st.success(f"CBS Transaction {reference_cbs} added!")

# Show ATM & CBS Data
st.subheader("📋 Transaction Data")
col1, col2 = st.columns(2)
with col1:
    st.write("🟢 **ATM Transactions**")
    st.dataframe(st.session_state.atm_data)
with col2:
    st.write("🔵 **CBS Transactions**")
    st.dataframe(st.session_state.cbs_data)

# Perform Reconciliation
if st.button("🔄 Process Reconciliation"):
    discrepancy_df = reconcile_data(st.session_state.atm_data, st.session_state.cbs_data)

    if not discrepancy_df.empty:
        st.subheader("⚠️ Detected Discrepancies")
        st.write(discrepancy_df)

        # Generate Excel Report
        excel_data = generate_excel_report(discrepancy_df)
        st.download_button(label="📥 Download Reconciliation Report", data=excel_data, file_name="Reconciliation_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # Visualization
        st.subheader("📊 Discrepancy Summary")
        fig, ax = plt.subplots()
        discrepancy_df["Issue"].value_counts().plot(kind="bar", ax=ax, color=["red", "orange", "blue"])
        st.pyplot(fig)
    else:
        st.success("✅ No Discrepancies Found!")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("👨‍💻 Developed by [Your Name]")
