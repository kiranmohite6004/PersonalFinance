import streamlit as st
import sqlite3
import base64
import requests
import os

# GitHub Configuration
GITHUB_TOKEN = st.secrets["github_token"]
GITHUB_USERNAME = "yourusername"
REPO_NAME = "your-repo"
FILE_PATH = "data.db"
BRANCH = "main"  # or 'master'

# SQLite DB Setup
conn = sqlite3.connect("data.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER
)
''')
conn.commit()

# Streamlit Form
with st.form("entry_form"):
    name = st.text_input("Name")
    age = st.number_input("Age", min_value=0, step=1)
    submitted = st.form_submit_button("Submit")

if submitted:
    # Insert into DB
    cursor.execute("INSERT INTO entries (name, age) VALUES (?, ?)", (name, age))
    conn.commit()
    st.success("Data saved locally!")

    # Read the updated DB and encode to base64
    with open("data.db", "rb") as f:
        content = base64.b64encode(f.read()).decode()

    # Get the file's SHA if it already exists (needed for updating)
    api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        sha = response.json()["sha"]
    else:
        sha = None  # File is new

    # Prepare data to upload
    commit_message = "Update DB from Streamlit app"
    payload = {
        "message": commit_message,
        "content": content,
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha

    # Upload to GitHub
    upload_response = requests.put(api_url, headers=headers, json=payload)

    if upload_response.status_code in [200, 201]:
        st.success("Database synced to GitHub!")
    else:
        st.error(f"Failed to upload: {upload_response.json()}")