import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# Database setup
conn = sqlite3.connect('finance_tracker.db', check_same_thread=False)
cursor = conn.cursor()

# Create table if not exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    category TEXT,
    subcategory TEXT,
    amount REAL,
    comment TEXT,
    created_at TEXT
)
''')
conn.commit()

# Category and subcategory mapping
category_subcategories = {
    "Inflow": ["Salary", "Rental Income", "Interest", "Others"],
    "Expenses": ["Home Expenses", "Others"],
    "Investment": ["PPF", "FD", "MF", "Post Office", "NPS", "Others"],
    "Insurance": ["LIC", "Health Insurance", "Others"],
    "Asset": ["Real Estate", "Gold", "Others"],
    "Liabilities": ["Car", "Bike", "Others"],
    "Miscellaneous": ["Others"]
}

st.title("📊 Personal Finance Tracker Dashboard")

# Sidebar year filter
st.sidebar.header("Filter by Year")
selected_year = st.sidebar.selectbox("Select Year", options=[str(y) for y in range(2020, datetime.now().year + 1)])

# Function to insert transaction
def insert_transaction(date, category, subcategory, amount, comment):
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO transactions (date, category, subcategory, amount, comment, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (date, category, subcategory, amount, comment, created_at))
    conn.commit()

# Function to display form for a category
def category_form(category):
    with st.expander(f"➕ Add {category} Transaction"):
        with st.form(f"{category}_form"):
            date = st.date_input("Transaction Date", value=datetime.today())
            subcategory = st.selectbox("Subcategory", category_subcategories[category])
            amount = st.number_input("Amount", min_value=0.0, format="%.2f")
            comment = st.text_area("Comment")
            submitted = st.form_submit_button("Add Transaction")
            if submitted:
                insert_transaction(date.strftime("%Y-%m-%d"), category, subcategory, amount, comment)
                st.success(f"{category} transaction added successfully!")

# Display forms for each category
for cat in category_subcategories.keys():
    category_form(cat)

# Load transactions for selected year
df = pd.read_sql_query("SELECT * FROM transactions", conn)
df['year'] = pd.to_datetime(df['date']).dt.year
filtered_df = df[df['year'] == int(selected_year)]

st.header(f"🗓️ Transactions for {selected_year}")
st.dataframe(filtered_df.drop(columns=['year']), use_container_width=True)

# Investment summary chart
investment_df = filtered_df[filtered_df['category'] == 'Investment']
if not investment_df.empty:
    st.subheader("📈 Investment Summary")
    chart_data = investment_df.groupby('subcategory')['amount'].sum()
    st.bar_chart(chart_data)

# Excel export
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.drop(columns=['year']).to_excel(writer, index=False, sheet_name='Transactions')
    processed_data = output.getvalue()
    return processed_data

st.download_button(
    label="📥 Download Transactions as Excel",
    data=convert_df_to_excel(filtered_df),
    file_name=f"transactions_{selected_year}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)