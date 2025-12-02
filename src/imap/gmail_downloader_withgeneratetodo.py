import imaplib
import email
import getpass
import sys
import os
from datetime import datetime, timedelta
from email.header import decode_header

# --- IMPORT SETUP ---
# Get the path to the 'src' folder and the 'todo_list' folder
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
todo_list_dir = os.path.join(src_dir, 'todo_list')

# Add 'src' to path so we can find the todo_list package
if src_dir not in sys.path:
    sys.path.append(src_dir)

# Add 'todo_list' to path so internal imports (like call_LLM) inside that folder work
if todo_list_dir not in sys.path:
    sys.path.append(todo_list_dir)

# Now we can import from the sibling folder
try:
    from todo_list.generate_todo_list import generate_todo_list
except ImportError as e:
    print(f"Warning: Could not import 'generate_todo_list'. Error: {e}")
    # Define a dummy function so the script doesn't crash if file is missing
    def generate_todo_list(emails):
        return "Error: generate_todo_list function not found."

def prompt_user():
    print("--- Gmail Auto-Labeler & Organizer ---")
    
    # 1. Credentials
    email_user = input("Enter your email address: ").strip()
    if not email_user: sys.exit("Email is required.")

    email_pass = getpass.getpass("Enter your App Password (hidden): ").strip()
    if not email_pass: sys.exit("Password is required.")

    # 2. Folder Selection
    print("\n--- Step 1: Select Folder ---")
    print("Press Enter for '[Gmail]/All Mail' (Searches Inbox + Archive + Categories).")
    print("Type 'INBOX' to search only the main Inbox.")
    folder_input = input("Folder Name: ").strip()
    folder = folder_input if folder_input else '"[Gmail]/All Mail"'

    # 3. Search Criteria
    print("\n--- Step 2: Search Criteria ---")
    print("Press Enter to default to LAST 7 DAYS, or type a custom query (e.g. SUBJECT \"Receipt\").")
    base_query = input("Search Query: ").strip()
    
    # 4. Unread Filter
    unread_only = input("Filter for UNREAD only? (y/n): ").lower().strip() == 'y'

    # Build the Query
    query_parts = []
    
    # Date/Base logic
    if base_query == '' or base_query.upper() == 'WEEK':
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        date_obj = datetime.now() - timedelta(days=7)
        month_str = months[date_obj.month - 1]
        since_date = f"{date_obj.day}-{month_str}-{date_obj.year}"
        query_parts.append(f'(SINCE "{since_date}")')
    else:
        query_parts.append(base_query)

    # Unread logic
    if unread_only:
        query_parts.append('UNSEEN')

    # Join with spaces
    final_query = ' '.join(query_parts)

    # 5. Label to Apply
    print("\n--- Step 3: Default Label ---")
    print("Enter the default label to apply.")
    label_name = input("Enter Label Name (e.g. 'Finance'): ").strip()
    if not label_name: sys.exit("Label name is required.")

    return email_user, email_pass, folder, final_query, label_name

def clean_header(header_value):
    """Decodes headers like Subject/From/In-Reply-To."""
    if not header_value: return ""
    decoded_list = decode_header(header_value)
    header_text = ""
    for token, encoding in decoded_list:
        if isinstance(token, bytes):
            header_text += token.decode(encoding or "utf-8", errors="ignore")
        else:
            header_text += str(token)
    return header_text

def is_original_email(msg):
    """Checks for 'In-Reply-To' header and 'Re:' in subject."""
    if msg['In-Reply-To']:
        return False
    subject = clean_header(msg['Subject'])
    if subject.lower().strip().startswith('re:'):
        return False
    return True

def process_emails():
    email_user, email_pass, folder, search_query, label_name = prompt_user()
    imap_server = 'imap.gmail.com'

    print(f"\nConnecting to {imap_server}...")
    
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_user, email_pass)
        
        # Select folder
        print(f"Selecting folder: {folder}...")
        resp, _ = mail.select(folder)
        if resp != 'OK':
            print(f"Error: Could not select folder '{folder}'. Falling back to 'INBOX'.")
            mail.select('INBOX')

        # --- PHASE 1: SEARCH & LABEL ---
        print(f"Searching with query: {search_query}...")
        resp, data = mail.search(None, search_query)

        if resp != 'OK':
            print("Search failed.")
            return []

        email_ids = data[0].split()
        original_emails_to_label = []
        
        print(f"Initial match: {len(email_ids)} emails. Checking for replies...")

        for e_id in email_ids:
            _, msg_data = mail.fetch(e_id, '(BODY.PEEK[HEADER.FIELDS (SUBJECT IN-REPLY-TO)])')
            
            if msg_data and isinstance(msg_data[0], tuple):
                msg = email.message_from_bytes(msg_data[0][1])
                
                if is_original_email(msg):
                    original_emails_to_label.append((e_id, clean_header(msg['Subject'])))

        count_originals = len(original_emails_to_label)
        print(f"Found {count_originals} ORIGINAL emails.")

        if count_originals > 0:
            print("\nPreview of Originals:")
            for _, subj in original_emails_to_label[:5]:
                print(f" - {subj}")
            
            confirm = input(f"Run labeling process on these {count_originals} emails? (y/n): ").lower()
            if confirm == 'y':
                print("Applying labels...")
                for e_id, subject_text in original_emails_to_label:
                    # Logic placeholder (using default label for now)
                    target_label = label_name 
                    imap_label_arg = f'"{target_label}"'
                    mail.store(e_id, '+X-GM-LABELS', imap_label_arg)
                print("Labels applied.")
            else:
                print("Skipped labeling.")
        else:
            print("No original emails found to label.")

        # --- PHASE 2: RETRIEVE 'BUSINESS' EMAILS ---
        print("\n--- Phase 2: Fetching 'Business' Labeled Emails ---")
        resp, business_data = mail.search(None, 'X-GM-LABELS "Business"')
        
        business_email_list = []

        if resp == 'OK':
            bus_ids = business_data[0].split()
            print(f"Found {len(bus_ids)} emails with label 'Business'. Fetching details...")
            
            for b_id in bus_ids:
                # Fetch BODY[TEXT] as well if your TODO generator needs the body content
                _, b_msg_data = mail.fetch(b_id, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM)])')
                if b_msg_data and isinstance(b_msg_data[0], tuple):
                    b_msg = email.message_from_bytes(b_msg_data[0][1])
                    subj = clean_header(b_msg['Subject'])
                    sender = clean_header(b_msg['From'])
                    
                    # Construct string for the TODO list generator
                    entry = f"From: {sender} | Subject: {subj}"
                    business_email_list.append(entry)
        
        mail.logout()
        return business_email_list

    except Exception as e:
        print(f"\nError: {e}")
        return []

if __name__ == "__main__":
    # 1. Run the IMAP process to get the list
    final_business_list = process_emails()
    
    # 2. Output the raw list
    print("\n" + "="*30)
    print("FINAL 'BUSINESS' EMAIL LIST")
    print("="*30)
    for item in final_business_list:
        print(item)

    # 3. Call the Todo List Generator
    if final_business_list:
        print("\n" + "="*30)
        print("GENERATING TODO LIST FROM EMAILS...")
        print("="*30)
        
        generated_todos = generate_todo_list(final_business_list)
        
        print(generated_todos)
    else:
        print("\nNo emails found to generate Todo list.")