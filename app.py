"""
Email to Todo List - Modern Glassmorphism UI
A beautiful Streamlit frontend for email classification and todo generation.
"""

import streamlit as st
import os
import html
import re
from pathlib import Path
from datetime import datetime


def clean_email_text(text: str) -> str:
    """
    Clean email text by removing any leftover HTML fragments.
    This is a safety net for display purposes.
    """
    if not text:
        return ""
    
    # Remove any leftover HTML tag fragments
    text = re.sub(r"<[^>]*>", "", text)  # Full tags
    text = re.sub(r"/?[a-zA-Z]+>", "", text)  # Closing fragments like "/div>"
    text = re.sub(r"</?[a-zA-Z]+", "", text)  # Opening fragments like "</div"
    text = re.sub(r"[<>]", "", text)  # Orphaned brackets
    
    # Clean up whitespace
    text = re.sub(r"\s+", " ", text)
    
    return text.strip()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Email to Todo",
    page_icon="",
    layout="wide"
)

# --- GLASSMORPHISM CSS STYLING ---
def inject_custom_css():
    """Load CSS from external file for better maintainability."""
    css_path = Path(__file__).parent / "styles.css"
    try:
        with open(css_path, "r") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("styles.css not found. Using default styling.")


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
def fetch_and_classify_emails(limit: int = 30):
    """Fetch emails and classify them."""
    try:
        from src.emails.read_mail import fetch_recent_emails
        from src.classifier.classify import classify
        
        with st.spinner("Fetching emails..."):
            emails = fetch_recent_emails(limit=limit)
        
        if not emails:
            st.warning("No emails found in your inbox.")
            return
        
        with st.spinner("Classifying emails..."):
            classified = classify(emails)
        
        st.session_state.emails = emails
        st.session_state.classified_emails = classified
        
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
        
        with st.spinner("Generating todo list..."):
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
    """Render a single email card with proper HTML escaping."""
    classification = email.get("classification", card_type)
    
    # HTML-escape all user content to prevent InvalidCharacterError
    sender = html.escape(str(email.get("from", "Unknown"))[:50])
    subject = html.escape(str(email.get("subject", "(No subject)")))
    
    # Format and escape date
    date_str = str(email.get("date", ""))
    try:
        if date_str:
            date_str = date_str.split(" (")[0]  # Remove timezone name
            date_str = date_str[:30]  # Truncate if too long
    except:
        pass
    date_escaped = html.escape(date_str)
    
    # Clean, truncate and escape body for preview
    body = str(email.get("body", ""))
    body = clean_email_text(body)  # Remove any leftover HTML fragments
    body_preview = body[:200] + "..." if len(body) > 200 else body
    body_preview_escaped = html.escape(body_preview)
    
    # Build attachment section with escaped filenames
    attachments_html = ""
    attachments = email.get("attachments", [])
    if attachments:
        attachment_chips = "".join([
            f'<span class="attachment-chip">{att.get("icon", "📎")} {html.escape(str(att.get("filename", "file"))[:20])}</span>'
            for att in attachments[:5]  # Limit to 5 attachments shown
        ])
        if len(attachments) > 5:
            attachment_chips += f'<span class="attachment-chip">+{len(attachments) - 5} more</span>'
        attachments_html = f'<div style="margin-top: 0.75rem;">{attachment_chips}</div>'
    
    # Badge HTML (classification only, no confidence)
    badge_class = "badge-business" if classification == "business" else "badge-personal"
    badge_text = classification.upper()
    
    st.markdown(f"""
    <div class="email-card {classification}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
            <span class="email-sender">{sender}</span>
            <div>
                <span class="badge {badge_class}">{badge_text}</span>
            </div>
        </div>
        <div class="email-subject">{subject}</div>
        <div class="email-date">{date_escaped}</div>
        <div class="email-body-preview">{body_preview_escaped}</div>
        {attachments_html}
    </div>
    """, unsafe_allow_html=True)
    
    # Expandable full content (using st.text for safe display)
    with st.expander("View full email"):
        st.text(f"From: {email.get('from', 'Unknown')}")
        st.text(f"Subject: {email.get('subject', '(No subject)')}")
        st.text(f"Date: {date_str}")
        st.markdown("---")
        st.text(body if body else "No content")
        
        # Attachment download buttons
        if attachments:
            st.markdown("**Attachments:**")
            for att_idx, att in enumerate(attachments):
                col1, col2 = st.columns([3, 1])
                # Create a unique key using email id, attachment index, and full attachment id
                email_id = email.get('id', 'unknown')
                att_id = att.get('attachmentId', f'att{att_idx}')
                unique_key = f"{email_id}_{att_idx}_{att_id}"
                
                with col1:
                    filename = html.escape(str(att.get('filename', 'file')))
                    st.markdown(f"[file] **{filename}** ({att.get('size', 0):,} bytes)")
                with col2:
                    if st.button(f"Download", key=f"dl_{unique_key}"):
                        try:
                            from src.emails.read_mail import download_attachment
                            data = download_attachment(email.get("id"), att.get("attachmentId"))
                            st.download_button(
                                label="Save",
                                data=data,
                                file_name=att.get("filename", "attachment"),
                                mime=att.get("mimeType", "application/octet-stream"),
                                key=f"save_{unique_key}"
                            )
                        except Exception as e:
                            st.error(f"Download failed: {e}")


def parse_and_render_todos(markdown_text: str):
    """
    Parse markdown todo list and render with interactive checkboxes.
    Supports formats like:
    - [ ] Task description
    - **Task** - metadata
    """
    if not markdown_text:
        return
    
    # Initialize checkbox state storage if not present
    if 'todo_checked' not in st.session_state:
        st.session_state.todo_checked = {}
    
    lines = markdown_text.split('\n')
    current_section = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Handle section headers (## or ###)
        if stripped.startswith('##'):
            header_text = stripped.lstrip('#').strip()
            st.markdown(f"**{header_text}**")
            current_section = header_text
            continue
        
        # Handle checkbox items: - [ ] or - [x]
        checkbox_match = re.match(r'^-\s*\[([ xX])\]\s*(.+)$', stripped)
        if checkbox_match:
            is_checked_in_text = checkbox_match.group(1).lower() == 'x'
            task_text = checkbox_match.group(2)
            
            # Create unique key for this checkbox
            checkbox_key = f"todo_cb_{i}_{hash(task_text) % 10000}"
            
            # Get current checked state (from session state or text)
            if checkbox_key not in st.session_state.todo_checked:
                st.session_state.todo_checked[checkbox_key] = is_checked_in_text
            
            # Render checkbox
            checked = st.checkbox(
                task_text,
                value=st.session_state.todo_checked[checkbox_key],
                key=checkbox_key
            )
            st.session_state.todo_checked[checkbox_key] = checked
            continue
        
        # Handle bullet points (non-checkbox): - text
        bullet_match = re.match(r'^-\s+(.+)$', stripped)
        if bullet_match:
            task_text = bullet_match.group(1)
            checkbox_key = f"todo_cb_{i}_{hash(task_text) % 10000}"
            
            if checkbox_key not in st.session_state.todo_checked:
                st.session_state.todo_checked[checkbox_key] = False
            
            checked = st.checkbox(
                task_text,
                value=st.session_state.todo_checked[checkbox_key],
                key=checkbox_key
            )
            st.session_state.todo_checked[checkbox_key] = checked
            continue
        
        # Handle other non-empty lines (plain text or other markdown)
        if stripped:
            st.markdown(stripped)


def render_todo_panel():
    """Render the todo panel in the right column."""
    st.markdown("### Todo List")
    
    # Generate button
    if st.button("Generate Todos", use_container_width=True, key="generate_todos_btn"):
        generate_todos()
    
    # Display todos
    if st.session_state.todos:
        # Parse and render with interactive checkboxes
        parse_and_render_todos(st.session_state.todos)
    else:
        st.markdown("*No todos yet. Fetch emails and click Generate Todos.*")


def render_login_screen():
    """Render the login screen."""
    st.markdown("""
    <div class="login-card">
        <h2 style="margin-bottom: 0.5rem;">Email to Todo</h2>
        <p style="color: #94a3b8; margin-bottom: 2rem;">
            Transform your inbox into an actionable todo list
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Sign in with Google", use_container_width=True):
            with st.spinner("Opening authentication..."):
                if do_auth():
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Authentication failed. Please try again.")


def render_main_app():
    """Render the main application with two-column layout."""
    # Header with flexbox layout - Title left, Logout button rendered via Streamlit
    st.markdown('''
    <div class="app-header">
        <div>
            <div class="main-title">Email to Todo</div>
            <div class="subtitle">Transform your inbox into organized action</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Logout button positioned via CSS (rendered in a container that CSS will position)
    st.markdown('<div class="logout-container">', unsafe_allow_html=True)
    if st.button("Logout", key="logout"):
        logout()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Main two-column layout: Email content (left) + Todo panel (right)
    email_col, todo_col = st.columns([3, 1])
    
    # LEFT COLUMN: Email content
    with email_col:
        # Row 1: Search input (full width)
        search = st.text_input(
            "Search emails",
            placeholder="Search by sender, subject, or content...",
            key="search_input",
            label_visibility="collapsed"
        )
        st.session_state.search_query = search
        
        # Row 2: Email count (with visible label, compact width via CSS)
        st.markdown('<div class="email-count-wrapper">', unsafe_allow_html=True)
        email_limit = st.number_input(
            "Number of emails to fetch:",
            min_value=5,
            max_value=100,
            value=30,
            step=5,
            key="email_count_input"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Row 3: Fetch button (on its own row)
        st.markdown('<div class="fetch-button-wrapper">', unsafe_allow_html=True)
        if st.button("Fetch Emails", key="fetch_btn"):
            fetch_and_classify_emails(limit=email_limit)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Check if we have emails
        if not st.session_state.classified_emails:
            st.markdown("""
            <div class="glass-card" style="text-align: center; padding: 4rem;">
                <h3 style="color: #e2e8f0; margin-bottom: 0.5rem;">No emails loaded</h3>
                <p style="color: #94a3b8;">Click Fetch Emails to scan your inbox and classify messages</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Email metrics
            business_emails = st.session_state.classified_emails.get("business", [])
            personal_emails = st.session_state.classified_emails.get("personal", [])
            
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{len(business_emails) + len(personal_emails)}</div>
                    <div class="metric-label">Total Emails</div>
                </div>
                """, unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                <div class="metric-card" style="border-color: rgba(245, 158, 11, 0.3);">
                    <div class="metric-value" style="color: #fbbf24;">{len(business_emails)}</div>
                    <div class="metric-label">Business</div>
                </div>
                """, unsafe_allow_html=True)
            with m3:
                st.markdown(f"""
                <div class="metric-card" style="border-color: rgba(6, 182, 212, 0.3);">
                    <div class="metric-value" style="color: #22d3ee;">{len(personal_emails)}</div>
                    <div class="metric-label">Personal</div>
                </div>
                """, unsafe_allow_html=True)
            with m4:
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
            tab_business, tab_personal = st.tabs(["Business", "Personal"])
            
            with tab_business:
                filtered = filter_emails(business_emails, st.session_state.search_query)
                if filtered:
                    for email in filtered:
                        render_email_card(email, "business")
                else:
                    st.markdown("""
                    <div class="empty-state">
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
                        <p>No personal emails found</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    # RIGHT COLUMN: Todo panel
    with todo_col:
        render_todo_panel()


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
