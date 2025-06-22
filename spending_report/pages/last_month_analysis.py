import streamlit as st
import pandas as pd

st.title("Analyze last month")

# Initialize session state to hold entries
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Date", "Description", "Category", "Subcategory", "Amount", "Balance"])

df = st.session_state.df
if df.empty:
    st.error("No data found")
    st.stop()

df["MonthYear"] = df["Date"].dt.to_period("M")
last_month = df["MonthYear"].max()
last_month_df = df[df["MonthYear"] == last_month]
prev_months_df = df[df["MonthYear"] != last_month]

spend_last_month = abs(last_month_df[last_month_df["Amount"] < 0]["Amount"].sum())
prev_spend_per_month = abs(prev_months_df[prev_months_df["Amount"] < 0].groupby("MonthYear")["Amount"].sum().mean())

income_last_month = last_month_df[last_month_df["Amount"] > 0]["Amount"].sum()
prev_income_per_month = prev_months_df[prev_months_df["Amount"] > 0].groupby("MonthYear")["Amount"].sum().mean()

income_change = (income_last_month - prev_income_per_month) / prev_income_per_month * 100 if prev_income_per_month else 0
spending_change = (spend_last_month - prev_spend_per_month) / prev_spend_per_month * 100 if prev_spend_per_month else 0

# --- UI Output ---
st.title("Monthly Financial Report")

st.subheader(f"Summary for {last_month}")
col1, col2, col3 = st.columns(3)
col1.metric("Total Income", f"{income_last_month:,.2f} GBP", f"{income_change:+.1f}% vs avg")
col2.metric("Total Spending", f"{spend_last_month:,.2f} GBP", f"{spending_change:+.1f}% vs avg", delta_color="inverse")
col3.metric("Net", f"{(income_last_month - spend_last_month):,.2f} GBP")

# --- Trend Chart ---
st.subheader("Monthly Trends")
monthly_summary = df.groupby("MonthYear")["Amount"].sum()
monthly_summary.index = monthly_summary.index.to_timestamp()
st.line_chart(monthly_summary)