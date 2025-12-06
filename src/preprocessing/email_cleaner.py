"""
Email cleaning and parsing utilities for preprocessing email datasets.
Handles header extraction, body cleaning, quoted reply removal, and signature removal.
"""

import re
from email import message_from_string
from email.utils import parsedate_to_datetime
from typing import Dict, Optional


def replace_urls_and_emails(text: str) -> str:
    """
    Replace URLs and email addresses with tokens to reduce vocabulary.
    
    Args:
        text: Input text
        
    Returns:
        Text with URLs replaced by [URL] and emails by [EMAIL]
    """
    # Replace URLs (http, https, www)
    text = re.sub(r'http\S+|www\.\S+', '[URL]', text)
    
    # Replace email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    return text


def parse_email_headers(raw_email: str) -> Dict[str, Optional[str]]:
    """
    Extract From, To, Subject, Date from raw email text.
    
    Args:
        raw_email: Raw email text including headers
        
    Returns:
        Dictionary with keys: from, to, subject, date
    """
    try:
        msg = message_from_string(raw_email)
        
        # Extract headers
        from_addr = msg.get('From', '')
        to_addr = msg.get('To', '')
        subject = msg.get('Subject', '')
        date = msg.get('Date', '')
        
        # Try to parse date
        try:
            if date:
                date_obj = parsedate_to_datetime(date)
                date = date_obj.isoformat()
        except:
            pass  # Keep original date string if parsing fails
            
        return {
            'from': from_addr,
            'to': to_addr,
            'subject': subject,
            'date': date
        }
    except Exception as e:
        # If parsing fails, return empty values
        return {
            'from': '',
            'to': '',
            'subject': '',
            'date': ''
        }


def extract_email_body(raw_email: str) -> str:
    """
    Extract body text from email, handling multipart messages.
    
    Args:
        raw_email: Raw email text
        
    Returns:
        Email body text
    """
    try:
        msg = message_from_string(raw_email)
        
        body = ""
        
        # Handle multipart messages
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                    
                # Get text/plain parts
                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body += payload.decode('utf-8', errors='ignore')
                    except:
                        try:
                            body += part.get_payload()
                        except:
                            pass
        else:
            # Single part message
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='ignore')
                else:
                    body = msg.get_payload()
            except:
                try:
                    body = msg.get_payload()
                except:
                    body = ""
                    
        return body if isinstance(body, str) else ""
        
    except Exception as e:
        # Fallback: try to extract everything after headers
        try:
            lines = raw_email.split('\n')
            body_start = 0
            for i, line in enumerate(lines):
                # Look for blank line separating headers from body
                if line.strip() == '' and i > 0:
                    body_start = i + 1
                    break
            return '\n'.join(lines[body_start:])
        except:
            return ""


def remove_quoted_replies(body: str) -> str:
    """
    Remove quoted reply blocks from email body.
    
    Args:
        body: Email body text
        
    Returns:
        Body with quoted replies removed
    """
    lines = body.split('\n')
    cleaned_lines = []
    skip_mode = False
    
    for line in lines:
        # Check for common quote patterns
        stripped = line.strip()
        
        # Lines starting with >
        if stripped.startswith('>'):
            continue
            
        # "On ... wrote:" pattern
        if re.match(r'^On\s+.+wrote:?\s*$', stripped, re.IGNORECASE):
            skip_mode = True
            continue
            
        # "From:" in forwarded messages
        if re.match(r'^-+\s*Forwarded\s+[Mm]essage\s*-+', stripped):
            skip_mode = True
            continue
            
        # "Original Message" header
        if re.match(r'^-+\s*Original\s+[Mm]essage\s*-+', stripped):
            skip_mode = True
            continue
            
        # Email-style headers in quoted section
        if skip_mode and re.match(r'^(From|To|Cc|Sent|Subject):\s*.+', stripped):
            continue
            
        # If we see substantial content after skip mode, resume
        if skip_mode and len(stripped) > 50 and not stripped.startswith('>'):
            skip_mode = False
            
        if not skip_mode:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def remove_signatures(body: str) -> str:
    """
    Remove email signatures from body text.
    
    Args:
        body: Email body text
        
    Returns:
        Body with signatures removed
    """
    # Common signature separators
    signature_patterns = [
        r'^--\s*$',  # Standard -- separator
        r'^_{3,}$',  # Underscore line
        r'^-{3,}$',  # Dash line
        r'^Sent from my',  # Mobile signatures
        r'^Get Outlook for',  # Outlook mobile
        r'^Sent via ',  # Various mobile clients
        r'^Thanks,?\s*$',  # Thanks/Thank you endings
        r'^Best regards?,?\s*$',
        r'^Regards?,?\s*$',
        r'^Sincerely,?\s*$',
        r'^Cheers,?\s*$',
        r'^Best,?\s*$',
    ]
    
    lines = body.split('\n')
    
    # Find the first signature indicator
    sig_start = len(lines)
    for i, line in enumerate(lines):
        stripped = line.strip()
        for pattern in signature_patterns:
            if re.match(pattern, stripped, re.IGNORECASE):
                sig_start = i
                break
        if sig_start < len(lines):
            break
    
    # Keep only lines before signature
    return '\n'.join(lines[:sig_start])


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    Args:
        text: Input text
        
    Returns:
        Text with normalized whitespace
    """
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace multiple newlines with double newline (paragraph separation)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Strip leading/trailing whitespace from each line
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Strip leading/trailing whitespace from entire text
    text = text.strip()
    
    return text


def clean_email_text(raw_email: str) -> Dict[str, str]:
    """
    Main email cleaning pipeline combining all cleaning functions.
    
    Args:
        raw_email: Raw email text including headers
        
    Returns:
        Dictionary with keys: from, to, subject, date, body_cleaned, email_text
    """
    # Parse headers
    headers = parse_email_headers(raw_email)
    
    # Extract body
    body = extract_email_body(raw_email)
    
    # Clean body
    body = remove_quoted_replies(body)
    body = remove_signatures(body)
    body = replace_urls_and_emails(body)
    body = normalize_whitespace(body)
    
    # Combine subject and body for model input
    subject = headers['subject']
    if subject:
        email_text = f"Subject: {subject}\n\n{body}"
    else:
        email_text = body
    
    return {
        'from': headers['from'],
        'to': headers['to'],
        'subject': headers['subject'],
        'date': headers['date'],
        'body_cleaned': body,
        'email_text': email_text
    }

