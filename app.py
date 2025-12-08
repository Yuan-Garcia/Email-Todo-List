import streamlit as st
import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# --- CONFIGURATION ---
st.set_page_config(page_title="Todo Generator", page_icon="📧")
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# --- AUTHENTICATION FUNCTIONS ---
def get_google_creds():
    """Handles the OAuth2 flow to log the user in."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                st.error("❌ 'credentials.json' not found. Please ask the admin for this file.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            # 0 means "pick any free port"
            creds = flow.run_local_server(port=5000, open_browser=False)
            
        # Save token for next time
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return creds

# --- MAIN APP UI ---
st.title("📧 Email to Todo List")

if 'creds' not in st.session_state:
    st.session_state.creds = None

# VIEW 1: LOGIN SCREEN
if not st.session_state.creds:
    st.info("Please sign in to access your emails.")
    if st.button("Sign in with Google"):
        st.session_state.creds = get_google_creds()
        st.rerun()

# VIEW 2: RUN PROGRAM
else:
    st.success("✅ Authenticated")
    
    if st.button("🚀 Run Generator"):
        with st.spinner("Scanning emails and generating tasks..."):
            try:
                # IMPORT YOUR FUNCTION HERE
                # Because we used pyproject.toml, we can import directly from 'emails'
                from emails.read_mail import fetch_recent_emails
                
                # Run your actual logic
                # You might need to pass 'st.session_state.creds' to your function
                # if your function expects credentials.
                fetch_recent_emails() 
                
                st.success("Done! Check your output.")
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
                
    if st.button("Logout"):
        if os.path.exists("token.json"):
            os.remove("token.json")
        st.session_state.creds = None
        st.rerun()