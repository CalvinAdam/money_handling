import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import io
from logger_config import get_logger


def clean_dataframe(df):
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
    df["Amount"] = df['Amount'].str.replace(',', '').astype(float)
    df["Balance"] = df['Balance'].str.replace(',', '').astype(float)
    df.dropna(subset=['Date', 'Amount'], inplace=True)
    df = df.sort_values(by=['Date', 'Amount'], ascending=False).reset_index(drop=True)
    st.session_state.df = df
    return df

logger = get_logger()

st.set_page_config(page_title="Monthly Spending Report", layout="centered")

# Sidebar
st.sidebar.title("Navigation")
selected_page = st.sidebar.radio("Go to", ["Spending Summary", "Manage Entries"])

if selected_page == "Spending Summary":

    st.title("Monthly Spending Report")
    st.write("Upload one or more CSV files to analyze your spending across multiple months.")

    uploaded_files = st.file_uploader("Choose one or more CSV files", type="csv", accept_multiple_files=True)

    if uploaded_files:
        all_data = []

        for file in uploaded_files:
            try:
                logger.info(f"Processing file: {file.name}")
                df = pd.read_csv(file, delimiter=",", encoding="latin1")
                logger.info(f"Loaded {len(df)} rows from {file.name}")
                df["Source File"] = file.name
                all_data.append(df)
            except Exception as e:
                logger.error(f"Error reading file {file.name}: {e}")
                st.error(f"Failed to load {file.name}. Check logs for more info.")
                continue

        if all_data:
            try:
                df = pd.concat(all_data, ignore_index=True)
                logger.info("All files successfully combined.")
                # Standard cleaning
                df = clean_dataframe(df)
                st.session_state.df = df
                logger.info(f"Data cleaned. Remaining rows: {len(df)}")
            except Exception as e:
                logger.exception("Error while processing data:")
                st.error("An error occurred while processing the data. Check logs for details.")

    if 'df' in st.session_state:
        try:
            df = st.session_state.df
            if df.empty:
                st.stop()
            spending_df = df[df['Amount'] < 0].copy()
            spending_df['Amount'] = spending_df['Amount'].abs()
            logger.info(f"Filtered to {len(spending_df)} spending transactions.")

            earning_df = df[df['Amount'] > 0].copy()
            logger.info(f"Filtered to {len(earning_df)} earning transactions.")

            # --- Summaries ---
            total_spent = spending_df['Amount'].sum()
            total_earned = earning_df['Amount'].sum()
            category_summary = spending_df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
            subcategory_summary = spending_df.groupby('Subcategory')['Amount'].sum().sort_values(ascending=False).head(5)

            # === Summary Output ===
            st.header("Summary")
            st.metric(label="Total Spent", value=f"${total_spent:,.2f}")
            st.metric(label="Total Earned", value=f"${total_earned:,.2f}")

            st.subheader("Spending by Category")
            st.dataframe(category_summary.rename("Total").reset_index().style.format({"Total": "${:,.2f}"}))

            st.subheader("Top 5 Subcategories")
            st.dataframe(subcategory_summary.rename("Total").reset_index().style.format({"Total": "${:,.2f}"}))

            # Pie Chart
            st.subheader("Pie Chart of Spending by Category")
            fig1, ax1 = plt.subplots(figsize=(8, 8))
            wedges, texts, autotexts = ax1.pie(
                category_summary,
                labels=category_summary.index,
                autopct='%1.1f%%',
                startangle=90,
                labeldistance=1.1,
                pctdistance=0.8,
                colors=plt.get_cmap('Set3').colors[:len(category_summary)],
                textprops={'fontsize': 12}
            )

            ax1.set_ylabel("")
            ax1.set_title("Spending by Category")
            st.pyplot(fig1)

            # Balance Over Time
            st.subheader("Balance Over Time")
            fig2, ax2 = plt.subplots()
            df_sorted = df.sort_values(["Source File", "Date"])
            sns.lineplot(data=df_sorted, x="Date", y="Balance", hue="Source File", ax=ax2)
            ax2.set_title("Balance Over Time (by file)")
            ax2.get_legend().remove()
            st.pyplot(fig2)

            logger.info("Report successfully generated.")
        except Exception as e:
            logger.exception(f"Error generating report: {e}")
            st.error("An error occurred while building the report. Check logs for details.")