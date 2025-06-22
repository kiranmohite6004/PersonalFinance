import streamlit as st
import requests
import base64
import datetime
import os

GITHUB_TOKEN = st.secrets["github_token"]
GITHUB_USERNAME = "kiranmohite6004"
REPO_NAME = "PersonalFinance"
FILE_PATH = "finance_tracker.db"
BRANCH = "main"

def upload_to_github():
    if not os.path.exists(FILE_PATH):
        st.error("DB file does not exist locally.")
        return

    # Read file and encode in base64
    with open(FILE_PATH, "rb") as file:
        content = file.read()
    b64_content = base64.b64encode(content).decode()

    # GitHub API URL
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{FILE_PATH}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Check if file exists to get SHA
    get_resp = requests.get(url, headers=headers)
    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

    data = {
        "message": f"Update {FILE_PATH} on {datetime.datetime.now().isoformat()}",
        "content": b64_content,
        "branch": BRANCH
    }
    if sha:
        data["sha"] = sha

    response = requests.put(url, headers=headers, json=data)

    if response.status_code in [200, 201]:
        st.success("Upload to GitHub successful!")
    else:
        st.error("Upload failed")
        st.error(f"Status Code: {response.status_code}")
        st.error(f"Details: {response.json()}")