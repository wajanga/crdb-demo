import streamlit as st
import pandas as pd
import requests
import io
import matplotlib.pyplot as plt

# Function to load data from uploaded file or URL
def load_data(uploaded_file, file_url):
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
    elif file_url:
        response = requests.get(file_url)
        df = pd.read_excel(io.BytesIO(response.content))
    else:
        return None
    return df

# Function to perform reconciliation
def reconcile_data(atm_data, cbs_data):
    discrepancies = []

    # Merging on REFERENCE
    merged_data = pd.merge(atm_data, cbs_data, on="REFERENCE", how="outer", suffixes=("_ATM", "_CBS"), indicator=True)

    for _, row in merged_data.iterrows():
        if row["_merge"] == "left_only":
            discrepancies.append({"REFERENCE": row["REFERENCE"], "Issue": "Missing in CBS"})
        elif row["_merge"] == "right_only":
            discrepancies.append({"REFERENCE": row["REFERENCE"], "Issue": "Missing in ATM"})
        elif row["DEBIT_ATM"] != row["DEBIT_CBS"] or row["CREDIT_ATM"] != row["CREDIT_CBS"]:
            discrepancies.append({"REFERENCE": row["REFERENCE"], "Issue": "Amount Mismatch"})

    return pd.DataFrame(discrepancies)

# Function to generate an Excel file
def generate_excel_report(discrepancy_df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        discrepancy_df.to_excel(writer, index=False, sheet_name="Discrepancies")
    return output.getvalue()

# Streamlit UI
st.title("🏦 ATM vs CBS Reconciliation Demo")

# File Upload Section
st.sidebar.header("📂 Upload or Provide URL")
atm_file = st.sidebar.file_uploader("Upload ATM Log (Excel)", type=["xlsx"])
cbs_file = st.sidebar.file_uploader("Upload CBS Report (Excel)", type=["xlsx"])
atm_url = st.sidebar.text_input("OR Enter ATM Log URL")
cbs_url = st.sidebar.text_input("OR Enter CBS Report URL")

if st.sidebar.button("Process Data"):
    # Load Data
    atm_data = load_data(atm_file, atm_url)
    cbs_data = load_data(cbs_file, cbs_url)

    if atm_data is not None and cbs_data is not None:
        st.success("✅ Files Loaded Successfully!")

        # Select relevant columns
        atm_data = atm_data[["REFERENCE", "DEBIT", "CREDIT", "CURRENCY"]]
        cbs_data = cbs_data[["REFERENCE", "DEBIT", "CREDIT", "CURRENCY"]]

        # Perform reconciliation
        discrepancy_df = reconcile_data(atm_data, cbs_data)

        if not discrepancy_df.empty:
            st.subheader("⚠️ Detected Discrepancies")
            st.write(discrepancy_df)

            # Generate Excel file
            excel_data = generate_excel_report(discrepancy_df)
            st.download_button(label="📥 Download Reconciliation Report", data=excel_data, file_name="Reconciliation_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # Visualization
            st.subheader("📊 Discrepancy Summary")
            fig, ax = plt.subplots()
            discrepancy_df["Issue"].value_counts().plot(kind="bar", ax=ax, color=["red", "orange", "blue"])
            st.pyplot(fig)
        else:
            st.success("✅ No Discrepancies Found!")

    else:
        st.error("⚠️ Please upload files or provide URLs.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("👨‍💻 Developed by [Your Name]")
