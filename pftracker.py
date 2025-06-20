import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime
from openpyxl.workbook import Workbook
import io

# Database setup
conn = sqlite3.connect("finance_tracker.db", check_same_thread=False)
c = conn.cursor()

# Create tables if they don't exist
c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                is_admin INTEGER DEFAULT 0
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                category TEXT,
                subcategory TEXT,
                amount REAL,
                comment TEXT,
                created_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )''')
conn.commit()

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    c.execute("SELECT id, password, is_admin FROM users WHERE username=?", (username,))
    result = c.fetchone()
    if result and result[1] == hash_password(password):
        return result[0], result[2]
    return None, None

def register_user(username, password):
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def add_transaction(user_id, date, category, subcategory, amount, comment):
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''INSERT INTO transactions (user_id, date, category, subcategory, amount, comment, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (user_id, date, category, subcategory, amount, comment, created_at))
    conn.commit()

def get_transactions(user_id=None, year=None):
    query = "SELECT id, user_id, date, category, subcategory, amount, comment, created_at FROM transactions"
    params = []
    if user_id is not None:
        query += " WHERE user_id=?"
        params.append(user_id)
    if year:
        if user_id is not None:
            query += " AND strftime('%Y', date)=?"
        else:
            query += " WHERE strftime('%Y', date)=?"
        params.append(str(year))
    query += " ORDER BY date"
    return pd.read_sql_query(query, conn, params=params)

def delete_transactions_by_ids(ids):
    c.executemany("DELETE FROM transactions WHERE id=?", [(i,) for i in ids])
    conn.commit()

# Streamlit UI
st.set_page_config(page_title="Personal Finance Tracker", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = ""
    st.session_state.is_admin = False

def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = ""
    st.session_state.is_admin = False
    st.rerun()

def login_screen():
    st.title("Login or Register")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            user_id, is_admin = verify_user(username, password)
            if user_id:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.session_state.is_admin = bool(is_admin)
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_user = st.text_input("New Username", key="reg_user")
        new_pass = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Register"):
            if register_user(new_user, new_pass):
                st.success("Registration successful. Please login.")
            else:
                st.error("Username already exists")

def dashboard():
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    if st.sidebar.button("Logout"):
        logout()

    st.title("📊 Personal Finance Tracker")

    categories = {
        "Inflow": [
            "Salary", "Rental Income", "Interest", "Dividends", "Capital Gains",
            "Freelance Income", "Business Income", "Others"
        ],
        "Outflow": [
            "Loan Repayment", "Credit Card Payment", "EMI", "Charity", "Others"
        ],
        "Investment": [
            "PPF", "FD", "MF", "Post Office", "NPS", "Stocks", "Bonds",
            "Real Estate Investment", "ETF", "Others"
        ],
        "Insurance": [
            "LIC", "Health Insurance", "Term Insurance", "Vehicle Insurance",
            "Travel Insurance", "Others"
        ],
        "Liabilities": [
            "Car - Maintenance & Repairs", "Bike - Maintenance & Repairs", "Home Loan", "Personal Loan",
            "Credit Card Debt", "Others"
        ],
        "Expenses": [
            "Home Expenses", "Groceries", "Utilities (Electricity)", "Utilities (Cable)", "Utilities (Gas)",
            "Utilities (Maintenance)", "Internet & Mobile", "Rent", "Education (Tuition, Books)",
            "Medical & Healthcare", "Transportation (Public Transit)", "Transportation (Car)", "Transportation (Bike)",
            "Dining & Restaurants","Entertainment (Movies, Events)", "Travel & Vacation",
            "Clothing & Accessories", "Personal Care (Salon, Spa)", "Childcare",
            "Subscriptions (Streaming, Software)", "Gifts & Donations", "Maintenance & Repairs", "Others"
        ],
        "Miscellaneous": [
            "Gifts", "Subscriptions", "One-time Purchases", "Others"
        ]
    }
    with st.expander("➕ Add Transaction"):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Transaction Date")
            category = st.selectbox("Category", list(categories.keys()))
        with col2:
            subcategory = st.selectbox("Subcategory", categories[category])
            amount = st.number_input("Amount", min_value=0.0, step=0.01)
        comment = st.text_area("Comment")
        if st.button("Add Transaction"):
            add_transaction(st.session_state.user_id, date.strftime("%Y-%m-%d"), category, subcategory, amount, comment)
            st.success("Transaction added successfully")

    year_filter = st.selectbox("Select Year", options=["All"] + sorted({datetime.strptime(d, "%Y-%m-%d").year for d in get_transactions(st.session_state.user_id)["date"]}))
    year = None if year_filter == "All" else int(year_filter)

    df = get_transactions(None if st.session_state.is_admin else st.session_state.user_id, year)

    st.subheader("📅 Transactions")
    display_df = df.drop(columns=["id", "user_id"])
    st.dataframe(display_df)

    if st.session_state.is_admin:
        st.info("Admin view: displaying all users' transactions")

    with st.expander("🗑️ Delete Transactions"):
        if not df.empty:
            df["select"] = False
            selected_rows = st.multiselect("Select Transactions to Delete", df.index, format_func=lambda x: f"{df.loc[x, 'date']} | {df.loc[x, 'category']} | {df.loc[x, 'subcategory']} | {df.loc[x, 'amount']}")
            if st.button("Delete Selected Transactions"):
                delete_ids = df.loc[selected_rows, "id"].tolist()
                delete_transactions_by_ids(delete_ids)
                st.success("Selected transactions deleted")
                st.rerun()
        else:
            st.info("No transactions available to delete.")

    with st.expander("📈 Year-on-Year Investment Summary"):
        inv_df = df[df["category"] == "Investment"]
        if not inv_df.empty:
            inv_df["year"] = pd.to_datetime(inv_df["date"]).dt.year
            summary = inv_df.groupby(["year", "subcategory"])["amount"].sum().unstack().fillna(0)
            st.bar_chart(summary)

    with st.expander("📥 Download Transactions as Excel"):
        output = io.BytesIO()
        export_df = df.drop(columns=["id", "user_id"])
        export_df.to_excel(output, index=False, engine='openpyxl')
        st.download_button("Download Excel", output.getvalue(), file_name="transactions.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if st.session_state.logged_in:
    dashboard()
else:
    login_screen()
