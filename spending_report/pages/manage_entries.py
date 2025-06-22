import streamlit as st
import pandas as pd


def construct_query():
    # Initialize the query string
    query_string = ""

    # Construct query for all active filters
    for f in st.session_state.filters:
        if f['value']:
            column = f['column']
            is_numeric = pd.api.types.is_numeric_dtype(df[column])
            is_datetime = pd.api.types.is_datetime64_any_dtype(df[column])
            if query_string:
                query_string += " and "

            # Construct query based on operator
            if f['operator'] in ["==", "!=", ">", "<", ">=", "<="]:
                if is_numeric or is_datetime:
                    query_string += f"{f['column']} {f['operator']} {f['value']}"
                else:
                    query_string += f"{f['column']}.str.strip() {f['operator']} '{f['value']}'"
            elif f['operator'] in ["contains", "not contains"]:
                query_string += f"{f['column']}.str.contains('{f['value']}', case=False, na=False)"
    return query_string

st.title("Manage Individual Entries")

# Initialize session state to hold entries
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Date", "Description", "Category", "Subcategory", "Amount", "Balance"])

df = st.session_state.df
# Show entries
st.subheader("Current Entries")
st.dataframe(df)

# Add new entry
st.subheader("Add New Entry")
with st.form("add_entry"):
    date = st.date_input("Date")
    description = st.text_input("Description")
    category = st.text_input("Category")
    subcategory = st.text_input("Subcategory")
    amount = st.number_input("Amount", value=0.0)
    balance = st.number_input("Balance", value=0.0)
    submitted = st.form_submit_button("Add Entry")
    if submitted:
        new_entry = {
            "Date": date,
            "Description": description,
            "Category": category,
            "Subcategory": subcategory,
            "Amount": amount,
            "Balance": balance
        }
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        st.session_state.df = df
        st.success("Entry added!")

# Modify entry
st.subheader("Modify Entry")

if 'filters' not in st.session_state:
    st.session_state.filters = [{
        'column': df.columns[0],
        'operator': '==',
        'value': ''
    }]


# Function to render filter UI elements
def render_filter(filter_index):
    f = st.session_state.filters[filter_index]

    col1, col2, col3 = st.columns(3)
    with col1:
        column = st.selectbox(f"Column {filter_index + 1}", df.columns,
                                        index=df.columns.get_loc(f['column']))
        is_numeric = pd.api.types.is_numeric_dtype(df[column])
        is_datetime = pd.api.types.is_datetime64_any_dtype(df[column])
        f['column'] = column
    with col2:
        if is_numeric or is_datetime:
            # Numeric or datetime value
            operators = ["==", "!=", ">", "<", ">=", "<="]
        else:
            # String value
            operators = ["==", "!=", "contains", "not contains"]
        if f['operator'] not in operators:
            # If the current selection is invalid for the new column default to ==
            f['operator'] = operators[0]
        f['operator'] = st.selectbox(f"Operator {filter_index + 1}",
                                          operators,
                                          index=operators.index(
                                              f['operator']))
    with col3:
        if is_numeric:
            # Numeric input
            f['value'] = st.number_input(f"Value {filter_index + 1}", key=filter_index)
        elif is_datetime:
            # Date input (No idea why I need to add to filter_index for key, but it breaks if I don't)
            value = st.date_input(f"Date {filter_index + 1}", value=None, key=filter_index+100000)
            if value is None:
                f['value'] = None
            else:
                f['value'] = value.strftime('%Y%m%d')
        else:
            # String input
            f['value'] = st.text_input(f"Value {filter_index + 1}", key=filter_index)

# Buttons to add/remove filters
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("Add Filter"):
        st.session_state.filters.append({'column': 'Amount', 'operator': '==', 'value': 0})

with col2:
    if len(st.session_state.filters) > 1 and st.button("Remove Last Filter"):
        st.session_state.filters.pop()


# Render existing filters
for i in range(len(st.session_state.filters)):
    render_filter(i)

# --- Search button ---
if st.button("Search"):
    try:
        query_string = construct_query()
        # If there is a query string, filter the DataFrame
        if query_string:
            st.session_state.query_string = query_string
    except Exception as e:
        st.error(f"Error applying filter: {e}")

if 'query_string' in st.session_state:
    query_string = st.session_state.query_string
    filtered_df = df.query(query_string)

    filtered_df["Select_Delete"] = False
    filtered_df["Select_Split"] = False
    st.success(f"{len(filtered_df)} result(s) found.")
    # Display editable table
    edited_df = st.data_editor(
        filtered_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Select_Delete": st.column_config.CheckboxColumn("Delete?", default=False),
            "Select_Split": st.column_config.CheckboxColumn("Split?", default=False),
            "Amount": st.column_config.NumberColumn(
                "Amount (GBP)",
                format="%.2f GBP",
            ),
            "Balance": st.column_config.NumberColumn(
                "Balance (GBP)",
                format="%.2f GBP",
            ),
        },
        key="editable_table"
    )

    if st.button("Save changes"):
        # TODO
        pass

    delete_rows = edited_df[edited_df["Select_Delete"] == True].index.tolist()

    if st.button("Delete Selected Rows"):
        df_after_delete = df.drop(index=delete_rows).reset_index(drop=True)
        st.session_state.df = df_after_delete
        st.success(f"Deleted {len(delete_rows)} row(s).")
        st.rerun()

    # --- Handle Split Selection (only 1 row allowed) ---
    split_rows = edited_df[edited_df["Select_Split"] == True]
    if len(split_rows) > 1:
        st.error("Only one row can be selected for splitting.")
    elif len(split_rows) == 1:
        row_to_split = split_rows.iloc[0]
        total_amount = row_to_split["Amount"]
        row_to_split_idx = row_to_split.index
        st.subheader("Split Row")
        st.info(f"Splitting row:")
        st.dataframe(row_to_split.drop(["Select_Split", "Select_Delete"]))

        num_splits = st.number_input("Number of rows to split into", min_value=2, max_value=10, value=2, step=1)

        split_amounts = []
        split_categories = []
        split_subcategories = []

        for i in range(num_splits):
            # Input for amounts, categories and subcategories
            if i == num_splits - 1:
                val = st.number_input(f"Amount for row {i + 1}", key=f"amount_{i}", value=total_amount-sum(split_amounts))
            else:
                val = st.number_input(f"Amount for row {i + 1}", key=f"amount_{i}")
            cat = st.text_input(f"Category for row {i + 1}", key=f"category_{i}")
            subcat = st.text_input(f"Subcategory for row {i + 1}", key=f"subcategory_{i}")
            split_amounts.append(val)
            split_categories.append(cat)
            split_subcategories.append(subcat)

        if st.button("Split Selected Row"):
            if abs(sum(split_amounts) - row_to_split["Amount"]) > 1e-6:
                st.error("Sum of new amounts must equal the original amount.")
            elif any(s == "" for s in split_amounts+split_subcategories):
                st.error("All new rows must have a category and a subcategory.")
            else:
                # Build new rows
                new_rows = []
                balance_change = 0
                for i in range(len(split_amounts)):
                    new_row = row_to_split.copy()
                    new_row["Amount"] = split_amounts[i]
                    new_row["Category"] = split_categories[i]
                    new_row["Subcategory"] = split_subcategories[i]
                    new_balance = row_to_split["Balance"] - total_amount + split_amounts[i] + balance_change
                    new_row["Balance"] = new_balance
                    balance_change += split_amounts[i]
                    new_rows.append(new_row)
                df_no_split = df.drop(index=split_rows.index).reset_index(drop=True)

                # Append new rows
                final_df = pd.concat([df_no_split, pd.DataFrame(new_rows)], ignore_index=True)
                final_df = final_df.sort_values(by=["Date", "Amount"], ascending=False).reset_index(drop=True)
                st.session_state.df = final_df
                st.success("Row successfully split.")
                st.rerun()



