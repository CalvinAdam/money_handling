import streamlit as st
import pandas as pd

st.title("Predict next month")

# Initialize session state to hold entries
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Date", "Description", "Category", "Subcategory", "Amount", "Balance"])

df = st.session_state.df
if df.empty:
    st.error("No data found")
    st.stop()

