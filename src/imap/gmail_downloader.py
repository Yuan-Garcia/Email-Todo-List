import imaplib
import email
import getpass
import sys
from datetime import datetime, timedelta
from email.header import decode_header

def prompt_user():
    print("--- Gmail Auto-Labeler & Organizer ---")
    
    # 1. Credentials
    email_user = input("Enter your email address: ").strip()
    if not email_user: sys.exit("Email is required.")

    email_pass = getpass.getpass("Enter your App Password (hidden): ").strip()
    if not email_pass: sys.exit("Password is required.")

    # 2. Search Criteria
    print("\n--- Step 1: Search Criteria ---")
    print("Press Enter to default to LAST 7 DAYS, or type a custom query (e.g. SUBJECT \"Receipt\").")
    base_query = input("Search Query: ").strip()
    
    # 3. Unread Filter
    unread_only = input("Filter for UNREAD only? (y/n): ").lower().strip() == 'y'

    # Build the Query
    query_parts = []
    
    # Date/Base logic
    if base_query == '' or base_query.upper() == 'WEEK':
        since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
        query_parts.append(f'(SINCE "{since_date}")')
    else:
        query_parts.append(base_query)

    # Unread logic
    if unread_only:
        query_parts.append('UNSEEN')

    # Join with spaces (IMAP requires space separation)
    final_query = ' '.join(query_parts)

    # 4. Label to Apply
    print("\n--- Step 2: Default Label ---")
    print("Enter the default label to apply (you can customize this per-email in the code later).")
    label_name = input("Enter Label Name (e.g. 'Finance'): ").strip()
    if not label_name: sys.exit("Label name is required.")

    return email_user, email_pass, final_query, label_name

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
    """
    Determines if an email is an original message or a reply.
    Checks for 'In-Reply-To' header and 'Re:' in subject.
    """
    # 1. Technical Check: 'In-Reply-To' header exists on replies
    if msg['In-Reply-To']:
        return False
        
    # 2. Visual Check: Subject starts with "Re:"
    subject = clean_header(msg['Subject'])
    if subject.lower().strip().startswith('re:'):
        return False

    return True

def process_emails():
    email_user, email_pass, search_query, label_name = prompt_user()
    imap_server = 'imap.gmail.com'

    print(f"\nConnecting to {imap_server}...")
    
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_user, email_pass)
        mail.select('INBOX')

        # --- PHASE 1: SEARCH & LABEL ---
        print(f"Searching with query: {search_query}...")
        resp, data = mail.search(None, search_query)

        if resp != 'OK':
            print("Search failed.")
            return []

        email_ids = data[0].split()
        
        # Filter for Originals in memory
        original_emails_to_label = []
        
        print(f"Initial match: {len(email_ids)} emails. Checking for replies...")

        for e_id in email_ids:
            # Fetch headers needed to check if it's a reply
            _, msg_data = mail.fetch(e_id, '(BODY.PEEK[HEADER.FIELDS (SUBJECT IN-REPLY-TO)])')
            
            if msg_data and isinstance(msg_data[0], tuple):
                msg = email.message_from_bytes(msg_data[0][1])
                
                if is_original_email(msg):
                    # Store tuple of (id, subject) so we can use subject for classification later
                    original_emails_to_label.append((e_id, clean_header(msg['Subject'])))

        count_originals = len(original_emails_to_label)
        print(f"Found {count_originals} ORIGINAL emails (excluded {len(email_ids) - count_originals} replies).")

        if count_originals > 0:
            print("\nPreview of Originals:")
            for _, subj in original_emails_to_label[:5]:
                print(f" - {subj}")
            
            confirm = input(f"Run labeling process on these {count_originals} emails? (y/n): ").lower()
            if confirm == 'y':
                print("Applying labels...")
                
                for e_id, subject_text in original_emails_to_label:
                    
                    # ======================================================
                    # TODO: PLACEHOLDER FOR CLASSIFIER LOGIC
                    # This is where we can add logic to label
                    # ======================================================
                    
                    # Example Logic:
                    # if "receipt" in subject_text.lower():
                    #     target_label = "Finance"
                    # elif "urgent" in subject_text.lower():
                    #     target_label = "Urgent"
                    # else:
                    #     target_label = label_name # Use the user's default input
                    
                    # Current Behavior: Always use the default input
                    target_label = label_name 
                    
                    # ======================================================
                    
                    imap_label_arg = f'"{target_label}"'
                    mail.store(e_id, '+X-GM-LABELS', imap_label_arg)
                    
                print("Labels applied.")
            else:
                print("Skipped labeling.")
        else:
            print("No original emails found to label.")

        # --- PHASE 2: RETRIEVE 'BUSINESS' EMAILS ---
        print("\n--- Phase 2: Fetching 'Business' Labeled Emails ---")
        # Search for the specific label "Business"
        # Note: X-GM-LABELS syntax requires the label name
        resp, business_data = mail.search(None, 'X-GM-LABELS "Business"')
        
        business_email_list = []

        if resp == 'OK':
            bus_ids = business_data[0].split()
            print(f"Found {len(bus_ids)} emails with label 'Business'. Fetching details...")
            
            for b_id in bus_ids:
                # Fetch Subject and From
                _, b_msg_data = mail.fetch(b_id, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM)])')
                if b_msg_data and isinstance(b_msg_data[0], tuple):
                    b_msg = email.message_from_bytes(b_msg_data[0][1])
                    subj = clean_header(b_msg['Subject'])
                    sender = clean_header(b_msg['From'])
                    
                    # Create string string for list
                    entry = f"From: {sender} | Subject: {subj}"
                    business_email_list.append(entry)
        
        mail.logout()
        return business_email_list

    except Exception as e:
        print(f"\nError: {e}")
        return []

if __name__ == "__main__":
    # Run the process
    final_business_list = process_emails()
    
    # Output the requested list
    print("\n" + "="*30)
    print("FINAL 'BUSINESS' EMAIL LIST")
    print("="*30)
    for item in final_business_list:
        print(item)