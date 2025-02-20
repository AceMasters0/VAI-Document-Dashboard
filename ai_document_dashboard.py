import streamlit as st
import pdfplumber
import openai
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd

# ✅ OpenAI API Key (Replace with your actual API key)
openai.api_key = "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"

import json
import streamlit as st
from google.oauth2 import service_account

# ✅ Load Google credentials from Streamlit Secrets
import streamlit as st
from google.oauth2 import service_account

# ✅ Load Google credentials from Streamlit Secrets
credentials = service_account.Credentials.from_service_account_info(
    {
        "type": "service_account",
        "project_id": st.secrets["google"]["project_id"],
        "private_key_id": st.secrets["google"]["private_key_id"],
        "private_key": st.secrets["google"]["private_key"],
        "client_email": st.secrets["google"]["client_email"],
        "client_id": st.secrets["google"]["client_id"],
        "auth_uri": st.secrets["google"]["auth_uri"],
        "token_uri": st.secrets["google"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["google"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["google"]["client_x509_cert_url"],
    },
    scopes=["https://www.googleapis.com/auth/drive.readonly"]
)


drive_service = build("drive", "v3", credentials=credentials)

# ✅ Streamlit UI
st.title("📑 AI-Powered Document Analysis Dashboard")

# ✅ Upload PDF or Select from Google Drive
uploaded_file = st.file_uploader("Upload a PDF for Analysis", type=["pdf"])

def list_drive_files():
    """Fetches all files inside the specified Google Drive folder."""
    folder_id = "1jpRS3lt76VhU_d8-c7EddPWL7fIY6rDw"  # Update with your folder ID
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents",
        fields="files(id, name, mimeType, modifiedTime)"
    ).execute()
    return results.get("files", [])

drive_files = list_drive_files()
if drive_files:
    selected_drive_file = st.selectbox("Or select a file from Google Drive:", [file['name'] for file in drive_files])
else:
    selected_drive_file = None

def extract_text_from_pdf(file):
    """Extracts text from an uploaded PDF file."""
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    return text

def analyze_text_with_ai(text):
    """Uses AI to analyze legal and financial documents."""
    prompt = f"""
    You are an expert in contract law and financial auditing.
    Please analyze the following document and provide:
    - Key legal terms and clauses
    - Potential risks or unusual terms
    - Any financial inconsistencies or red flags

    Document Text:
    {text[:3000]}
    """
    
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

if uploaded_file or selected_drive_file:
    if uploaded_file:
        st.write("Analyzing uploaded file...")
        extracted_text = extract_text_from_pdf(uploaded_file)
    else:
        file_id = [file['id'] for file in drive_files if file['name'] == selected_drive_file][0]
        request = drive_service.files().get_media(fileId=file_id)
        with open("temp.pdf", "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        extracted_text = extract_text_from_pdf("temp.pdf")
        os.remove("temp.pdf")

    ai_analysis = analyze_text_with_ai(extracted_text)
    st.subheader("📊 AI Analysis")
    st.write(ai_analysis)

    # ✅ Save AI findings to CSV
    if st.button("Download Report as CSV"):
        df = pd.DataFrame({"AI Findings": [ai_analysis]})
        df.to_csv("ai_analysis.csv", index=False)
        st.download_button(
            label="Download CSV",
            data=df.to_csv(index=False),
            file_name="ai_analysis.csv",
            mime="text/csv"
        )

st.write("👆 Upload a PDF or select a file from Google Drive to begin analysis.")
