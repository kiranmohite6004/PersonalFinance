import streamlit as st
import requests
import base64
import os
import datetime

GITHUB_USERNAME = "kiranmohite6004"
REPO_NAME = "PersonalFinance"
FILE_PATH = "finance_tracker.db"
BRANCH = "main"
GITHUB_TOKEN = st.secrets["github_token"]

def upload_to_github():
    st.write("Checking directory:", os.listdir())

    if not os.path.exists(FILE_PATH):
        st.error(f"{FILE_PATH} not found!")
        return

    with open(FILE_PATH, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{FILE_PATH}"
    st.write("Upload URL:", url)

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    payload = {
        "message": f"Upload at {datetime.datetime.now().isoformat()}",
        "content": content,
        "branch": BRANCH
    }

    response = requests.put(url, headers=headers, json=payload)
    st.write("Status code:", response.status_code)
    st.json(response.json())

if st.button("Upload DB to GitHub"):
    upload_to_github()