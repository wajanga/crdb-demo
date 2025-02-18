# import streamlit as st

# st.title("🎈 My new app")
# st.write(
#     "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
# )

import streamlit as st
import pandas as pd
import requests

# Title of the dashboard
st.title("🚀 ATM Reconciliation Dashboard")

# Load the reconciliation report
@st.cache_data
def load_data():
    return pd.read_excel("/mnt/data/Reconciliation_Report.xlsx")

data = load_data()

# Display summary metrics
st.metric("Total Transactions", len(data))
st.metric("Discrepancies Found", len(data[data["Discrepancy"] != "Match"]))

# Filter options
filter_option = st.selectbox("Filter Transactions", ["All", "Missing in CBS", "Missing in ATM", "Amount Mismatch"])

if filter_option != "All":
    data = data[data["Discrepancy"] == filter_option]

# Display data table
st.dataframe(data)

# Button to trigger reconciliation workflow in n8n
if st.button("🔄 Re-run Reconciliation"):
    response = requests.post("https://n8n-server-url/webhook/reconciliation")
    if response.status_code == 200:
        st.success("Reconciliation Process Triggered Successfully! 🎉")
    else:
        st.error("Failed to trigger workflow. Please check the n8n server.")

# Export button
st.download_button("📥 Download Report", data.to_csv(index=False), "reconciliation_report.csv")

st.markdown("**Built with ❤️ using n8n + Streamlit**")
