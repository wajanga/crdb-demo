import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt

# Generate Fake ATM & CBS Data
def generate_fake_data():
    # Fake ATM Transactions
    atm_data = pd.DataFrame([
        {"REFERENCE": "1001", "DEBIT": 100000, "CREDIT": 0, "CURRENCY": "TZS"},
        {"REFERENCE": "1002", "DEBIT": 50000, "CREDIT": 0, "CURRENCY": "TZS"},
        {"REFERENCE": "1003", "DEBIT": 200000, "CREDIT": 0, "CURRENCY": "TZS"},
        {"REFERENCE": "1004", "DEBIT": 75000, "CREDIT": 0, "CURRENCY": "TZS"},
    ])

    # Fake CBS Transactions (With Intentional Errors)
    cbs_data = pd.DataFrame([
        {"REFERENCE": "1001", "DEBIT": 100000, "CREDIT": 0, "CURRENCY": "TZS"},
        {"REFERENCE": "1002", "DEBIT": 45000, "CREDIT": 0, "CURRENCY": "TZS"},  # Mismatch
        {"REFERENCE": "1004", "DEBIT": 75000, "CREDIT": 0, "CURRENCY": "TZS"},
        {"REFERENCE": "1005", "DEBIT": 30000, "CREDIT": 0, "CURRENCY": "TZS"},  # Extra Transaction in CBS
    ])

    return atm_data, cbs_data

# Function to perform reconciliation
def reconcile_data(atm_data, cbs_data):
    discrepancies = []

    # Merge Data
    merged_data = pd.merge(atm_data, cbs_data, on="REFERENCE", how="outer", suffixes=("_ATM", "_CBS"), indicator=True)

    for _, row in merged_data.iterrows():
        if row["_merge"] == "left_only":
            discrepancies.append({"REFERENCE": row["REFERENCE"], "Issue": "Missing in CBS"})
        elif row["_merge"] == "right_only":
            discrepancies.append({"REFERENCE": row["REFERENCE"], "Issue": "Missing in ATM"})
        elif row["DEBIT_ATM"] != row["DEBIT_CBS"]:
            discrepancies.append({"REFERENCE": row["REFERENCE"], "Issue": "Amount Mismatch"})

    return pd.DataFrame(discrepancies)

# Function to generate Excel file for download
def generate_excel_report(discrepancy_df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        discrepancy_df.to_excel(writer, index=False, sheet_name="Discrepancies")
    return output.getvalue()

# Streamlit UI
st.title("🏦 ATM vs CBS Reconciliation Demo (Fixed Data)")

# Load Fake Data
atm_data, cbs_data = generate_fake_data()

# Show Sample Data
st.subheader("📋 Sample ATM & CBS Data")
col1, col2 = st.columns(2)
with col1:
    st.write("🟢 **ATM Transactions**")
    st.dataframe(atm_data)
with col2:
    st.write("🔵 **CBS Transactions**")
    st.dataframe(cbs_data)

# Perform Reconciliation
discrepancy_df = reconcile_data(atm_data, cbs_data)

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
