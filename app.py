"""
Email to Todo List - Modern Glassmorphism UI
A beautiful Streamlit frontend for email classification and todo generation.
"""

import streamlit as st
import os
import base64
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Email → Todo",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GLASSMORPHISM CSS STYLING ---
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    /* === GLOBAL STYLES === */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* === GLASS CARD BASE === */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    /* === EMAIL CARDS === */
    .email-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 1.25rem;
        margin-bottom: 0.75rem;
        transition: all 0.3s ease;
    }
    
    .email-card:hover {
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(255, 255, 255, 0.15);
        transform: translateX(4px);
    }
    
    .email-card.business {
        border-left: 3px solid #f59e0b;
        box-shadow: 0 4px 20px rgba(245, 158, 11, 0.1);
    }
    
    .email-card.business:hover {
        box-shadow: 0 6px 30px rgba(245, 158, 11, 0.2);
    }
    
    .email-card.personal {
        border-left: 3px solid #06b6d4;
        box-shadow: 0 4px 20px rgba(6, 182, 212, 0.1);
    }
    
    .email-card.personal:hover {
        box-shadow: 0 6px 30px rgba(6, 182, 212, 0.2);
    }
    
    .email-sender {
        color: #e2e8f0;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.25rem;
    }
    
    .email-subject {
        color: #f8fafc;
        font-weight: 500;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    
    .email-date {
        color: #94a3b8;
        font-size: 0.8rem;
        margin-bottom: 0.75rem;
    }
    
    .email-body-preview {
        color: #cbd5e1;
        font-size: 0.9rem;
        line-height: 1.5;
        opacity: 0.8;
    }
    
    /* === BADGES === */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-business {
        background: rgba(245, 158, 11, 0.2);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    .badge-personal {
        background: rgba(6, 182, 212, 0.2);
        color: #22d3ee;
        border: 1px solid rgba(6, 182, 212, 0.3);
    }
    
    .badge-confidence {
        background: rgba(139, 92, 246, 0.2);
        color: #a78bfa;
        border: 1px solid rgba(139, 92, 246, 0.3);
        margin-left: 0.5rem;
    }
    
    /* === ATTACHMENT CHIPS === */
    .attachment-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 0.4rem 0.8rem;
        margin: 0.25rem;
        font-size: 0.8rem;
        color: #e2e8f0;
        transition: all 0.2s ease;
    }
    
    .attachment-chip:hover {
        background: rgba(255, 255, 255, 0.12);
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    /* === SIDEBAR STYLING === */
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    section[data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }
    
    /* === TODO ITEM === */
    .todo-item {
        background: rgba(139, 92, 246, 0.1);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s ease;
    }
    
    .todo-item:hover {
        background: rgba(139, 92, 246, 0.15);
        border-color: rgba(139, 92, 246, 0.3);
    }
    
    .todo-priority-high {
        border-left: 3px solid #ef4444;
    }
    
    .todo-priority-medium {
        border-left: 3px solid #f59e0b;
    }
    
    .todo-priority-low {
        border-left: 3px solid #22c55e;
    }
    
    /* === BUTTONS === */
    .stButton > button {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.8) 0%, rgba(168, 85, 247, 0.8) 100%);
        color: white;
        border: 1px solid rgba(139, 92, 246, 0.5);
        border-radius: 12px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        font-family: 'Plus Jakarta Sans', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(139, 92, 246, 0.5);
        border-color: rgba(139, 92, 246, 0.8);
    }
    
    /* Secondary button style */
    .secondary-btn > button {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: none !important;
    }
    
    .secondary-btn > button:hover {
        background: rgba(255, 255, 255, 0.12) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* === SEARCH INPUT === */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        color: #f8fafc;
        padding: 0.75rem 1rem;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: rgba(139, 92, 246, 0.5);
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.2);
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #64748b;
    }
    
    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 16px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 12px;
        color: #94a3b8;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.05);
        color: #e2e8f0;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(139, 92, 246, 0.2) !important;
        color: #a78bfa !important;
        border: 1px solid rgba(139, 92, 246, 0.3);
    }
    
    /* === EXPANDER === */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        color: #e2e8f0 !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 0 0 12px 12px;
    }
    
    /* === SPINNER === */
    .stSpinner > div {
        border-color: #8b5cf6 transparent transparent transparent;
    }
    
    /* === TITLE & HEADERS === */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #f8fafc 0%, #a78bfa 50%, #22d3ee 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #94a3b8;
        font-size: 1rem;
        font-weight: 400;
        margin-bottom: 2rem;
    }
    
    /* === METRICS === */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #f8fafc;
    }
    
    .metric-label {
        font-size: 0.8rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* === SCROLLBAR === */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(139, 92, 246, 0.3);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(139, 92, 246, 0.5);
    }
    
    /* === ALERTS === */
    .stAlert {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
    }
    
    /* === DOWNLOAD BUTTON === */
    .download-btn {
        background: rgba(34, 197, 94, 0.2);
        border: 1px solid rgba(34, 197, 94, 0.3);
        color: #4ade80;
        padding: 0.3rem 0.6rem;
        border-radius: 8px;
        font-size: 0.75rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .download-btn:hover {
        background: rgba(34, 197, 94, 0.3);
    }
    
    /* === LOGIN CARD === */
    .login-card {
        max-width: 400px;
        margin: 4rem auto;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 3rem;
        text-align: center;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
    }
    
    .login-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    
    /* === EMPTY STATE === */
    .empty-state {
        text-align: center;
        padding: 3rem;
        color: #64748b;
    }
    
    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }
    </style>
    """, unsafe_allow_html=True)


# --- SESSION STATE INITIALIZATION ---
def init_session_state():
    """Initialize all session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'emails' not in st.session_state:
        st.session_state.emails = None
    if 'classified_emails' not in st.session_state:
        st.session_state.classified_emails = None
    if 'todos' not in st.session_state:
        st.session_state.todos = None
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'loading' not in st.session_state:
        st.session_state.loading = False


# --- AUTHENTICATION ---
def check_auth():
    """Check if user is authenticated by looking for token file."""
    from pathlib import Path
    token_paths = [
        Path("token.json"),
        Path("src/emails/token.json"),
    ]
    for path in token_paths:
        if path.exists():
            return True
    return False


def do_auth():
    """Perform OAuth authentication."""
    try:
        from src.emails.auth import get_creds
        creds = get_creds()
        return creds is not None
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        return False


def logout():
    """Remove token files and reset session."""
    from pathlib import Path
    token_paths = [
        Path("token.json"),
        Path("src/emails/token.json"),
    ]
    for path in token_paths:
        if path.exists():
            path.unlink()
    st.session_state.authenticated = False
    st.session_state.emails = None
    st.session_state.classified_emails = None
    st.session_state.todos = None


# --- EMAIL FETCHING & CLASSIFICATION ---
def fetch_and_classify_emails():
    """Fetch emails and classify them."""
    try:
        from src.emails.read_mail import fetch_recent_emails
        from src.classifier.classify import classify
        
        with st.spinner("📬 Fetching your emails..."):
            emails = fetch_recent_emails(limit=30)
        
        if not emails:
            st.warning("No emails found in your inbox.")
            return
        
        with st.spinner("🧠 Classifying emails..."):
            classified = classify(emails)
        
        st.session_state.emails = emails
        st.session_state.classified_emails = classified
        
        business_count = len(classified.get("business", []))
        personal_count = len(classified.get("personal", []))
        st.success(f"✨ Found {business_count} business and {personal_count} personal emails!")
        
    except Exception as e:
        st.error(f"Error fetching emails: {e}")


# --- TODO GENERATION ---
def generate_todos():
    """Generate todos from business emails."""
    try:
        from src.todo_list.generate_todo_list import generate_todo_list, format_emails_for_prompt
        
        if not st.session_state.classified_emails:
            st.warning("Please fetch emails first!")
            return
        
        business_emails = st.session_state.classified_emails.get("business", [])
        if not business_emails:
            st.warning("No business emails to generate todos from.")
            return
        
        with st.spinner("✍️ Generating your todo list..."):
            formatted = format_emails_for_prompt(business_emails)
            todos = generate_todo_list(formatted)
        
        st.session_state.todos = todos
        
    except Exception as e:
        st.error(f"Error generating todos: {e}")


# --- SEARCH FUNCTION ---
def filter_emails(emails, query):
    """Filter emails by search query across from, subject, and body."""
    if not query or not emails:
        return emails
    
    query_lower = query.lower()
    filtered = []
    
    for email in emails:
        if (query_lower in email.get("from", "").lower() or
            query_lower in email.get("subject", "").lower() or
            query_lower in email.get("body", "").lower()):
            filtered.append(email)
    
    return filtered


# --- RENDER FUNCTIONS ---
def render_email_card(email, card_type="business"):
    """Render a single email card."""
    classification = email.get("classification", card_type)
    confidence = email.get("confidence", 0)
    
    # Format date
    date_str = email.get("date", "")
    try:
        # Try to parse and format the date
        if date_str:
            # Handle various date formats
            date_str = date_str.split(" (")[0]  # Remove timezone name
            date_str = date_str[:30]  # Truncate if too long
    except:
        pass
    
    # Truncate body for preview
    body = email.get("body", "")
    body_preview = body[:200] + "..." if len(body) > 200 else body
    
    # Build attachment section
    attachments_html = ""
    attachments = email.get("attachments", [])
    if attachments:
        attachment_chips = "".join([
            f'<span class="attachment-chip">{att.get("icon", "📎")} {att.get("filename", "file")[:20]}</span>'
            for att in attachments[:5]  # Limit to 5 attachments shown
        ])
        if len(attachments) > 5:
            attachment_chips += f'<span class="attachment-chip">+{len(attachments) - 5} more</span>'
        attachments_html = f'<div style="margin-top: 0.75rem;">{attachment_chips}</div>'
    
    # Badge HTML
    badge_class = "badge-business" if classification == "business" else "badge-personal"
    badge_text = classification.upper()
    confidence_pct = f"{confidence * 100:.0f}%" if confidence else ""
    
    st.markdown(f"""
    <div class="email-card {classification}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
            <span class="email-sender">{email.get("from", "Unknown")[:50]}</span>
            <div>
                <span class="badge {badge_class}">{badge_text}</span>
                {f'<span class="badge badge-confidence">{confidence_pct}</span>' if confidence_pct else ''}
            </div>
        </div>
        <div class="email-subject">{email.get("subject", "(No subject)")}</div>
        <div class="email-date">📅 {date_str}</div>
        <div class="email-body-preview">{body_preview}</div>
        {attachments_html}
    </div>
    """, unsafe_allow_html=True)
    
    # Expandable full content
    with st.expander("View full email"):
        st.markdown(f"**From:** {email.get('from', 'Unknown')}")
        st.markdown(f"**Subject:** {email.get('subject', '(No subject)')}")
        st.markdown(f"**Date:** {date_str}")
        st.markdown("---")
        st.markdown(body if body else "*No content*")
        
        # Attachment download buttons
        if attachments:
            st.markdown("**Attachments:**")
            for att in attachments:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"{att.get('icon', '📎')} **{att.get('filename', 'file')}** ({att.get('size', 0):,} bytes)")
                with col2:
                    if st.button(f"Download", key=f"dl_{email.get('id', '')}_{att.get('attachmentId', '')[:8]}"):
                        try:
                            from src.emails.read_mail import download_attachment
                            data = download_attachment(email.get("id"), att.get("attachmentId"))
                            st.download_button(
                                label="💾 Save",
                                data=data,
                                file_name=att.get("filename", "attachment"),
                                mime=att.get("mimeType", "application/octet-stream"),
                                key=f"save_{email.get('id', '')}_{att.get('attachmentId', '')[:8]}"
                            )
                        except Exception as e:
                            st.error(f"Download failed: {e}")


def render_todo_sidebar():
    """Render the todo sidebar."""
    st.markdown("### ✨ Todo List")
    
    # Generate button
    if st.button("🚀 Generate Todos", use_container_width=True):
        generate_todos()
    
    st.markdown("---")
    
    # Display todos
    if st.session_state.todos:
        # Parse and display the todo list
        todos_text = st.session_state.todos
        st.markdown(f"""
        <div style="
            background: rgba(139, 92, 246, 0.1);
            border: 1px solid rgba(139, 92, 246, 0.2);
            border-radius: 16px;
            padding: 1rem;
            font-size: 0.9rem;
            color: #e2e8f0;
            white-space: pre-wrap;
            max-height: 60vh;
            overflow-y: auto;
        ">
{todos_text}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📝</div>
            <p>No todos yet.<br>Fetch emails and click "Generate Todos"!</p>
        </div>
        """, unsafe_allow_html=True)


def render_login_screen():
    """Render the login screen."""
    st.markdown("""
    <div class="login-card">
        <div class="login-icon">📧</div>
        <h2 style="margin-bottom: 0.5rem;">Email → Todo</h2>
        <p style="color: #94a3b8; margin-bottom: 2rem;">
            Transform your inbox into an actionable todo list
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔐 Sign in with Google", use_container_width=True):
            with st.spinner("Opening authentication..."):
                if do_auth():
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Authentication failed. Please try again.")


def render_main_app():
    """Render the main application."""
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="main-title">📧 Email → Todo</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Transform your inbox chaos into organized action</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Logout", key="logout"):
            logout()
            st.rerun()
    
    # Sidebar with Todo List
    with st.sidebar:
        render_todo_sidebar()
    
    # Main content area
    # Search and Fetch row
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input(
            "Search emails",
            placeholder="🔍 Search by sender, subject, or content...",
            key="search_input",
            label_visibility="collapsed"
        )
        st.session_state.search_query = search
    with col2:
        if st.button("📬 Fetch Emails", use_container_width=True):
            fetch_and_classify_emails()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Check if we have emails
    if not st.session_state.classified_emails:
        st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 4rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📭</div>
            <h3 style="color: #e2e8f0; margin-bottom: 0.5rem;">No emails loaded</h3>
            <p style="color: #94a3b8;">Click "Fetch Emails" to scan your inbox and classify messages</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Email metrics
    business_emails = st.session_state.classified_emails.get("business", [])
    personal_emails = st.session_state.classified_emails.get("personal", [])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(business_emails) + len(personal_emails)}</div>
            <div class="metric-label">Total Emails</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-color: rgba(245, 158, 11, 0.3);">
            <div class="metric-value" style="color: #fbbf24;">{len(business_emails)}</div>
            <div class="metric-label">Business</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="border-color: rgba(6, 182, 212, 0.3);">
            <div class="metric-value" style="color: #22d3ee;">{len(personal_emails)}</div>
            <div class="metric-label">Personal</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        total_attachments = sum(
            len(e.get("attachments", [])) 
            for e in business_emails + personal_emails
        )
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_attachments}</div>
            <div class="metric-label">Attachments</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs for Business/Personal
    tab_business, tab_personal = st.tabs(["💼 Business", "👤 Personal"])
    
    with tab_business:
        filtered = filter_emails(business_emails, st.session_state.search_query)
        if filtered:
            for email in filtered:
                render_email_card(email, "business")
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">💼</div>
                <p>No business emails found</p>
            </div>
            """, unsafe_allow_html=True)
    
    with tab_personal:
        filtered = filter_emails(personal_emails, st.session_state.search_query)
        if filtered:
            for email in filtered:
                render_email_card(email, "personal")
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">👤</div>
                <p>No personal emails found</p>
            </div>
            """, unsafe_allow_html=True)


# --- MAIN ---
def main():
    inject_custom_css()
    init_session_state()
    
    # Check authentication
    if check_auth():
        st.session_state.authenticated = True
    
    if st.session_state.authenticated:
        render_main_app()
    else:
        render_login_screen()


if __name__ == "__main__":
    main()
