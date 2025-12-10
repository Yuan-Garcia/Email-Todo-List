import re
import time
import base64
from typing import List, Dict, Optional, Any

from email.header import decode_header, make_header
from googleapiclient.discovery import build

from .auth import get_creds  # your existing OAuth helper

# Module-level service cache for attachment downloads
_gmail_service = None


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _decode_header(value: Optional[str]) -> str:
    """
    Safely decode MIME-encoded headers (e.g., Subject, From).
    """
    if not value:
        return ""
    return str(make_header(decode_header(value)))


def strip_replies(email_text: str) -> str:
    """
    Given a plain-text email body string, return only the original
    top-level message, removing quoted replies and older message history.
    """
    reply_header_patterns = [
        re.compile(r"^\s*On .+ wrote:\s*$"),                        # Gmail style
        re.compile(r"^\s*-{2,}\s*Original Message\s*-{2,}\s*$", re.IGNORECASE),
        re.compile(r"^\s*From:\s+.+$", re.IGNORECASE),
        re.compile(r"^\s*Sent:\s+.+$", re.IGNORECASE),
        re.compile(r"^\s*To:\s+.+$", re.IGNORECASE),
        re.compile(r"^\s*Subject:\s+.+$", re.IGNORECASE),
        re.compile(r"^\s*-----Original Message-----\s*$", re.IGNORECASE),
    ]

    def looks_like_reply_header(line: str) -> bool:
        return any(p.match(line) for p in reply_header_patterns)

    if not email_text:
        return ""

    lines = email_text.splitlines()
    kept: List[str] = []

    for line in lines:
        # Stop if this line indicates the start of old quoted content
        if looks_like_reply_header(line):
            break

        # Skip classic quoted lines (e.g., "> previous message")
        if line.lstrip().startswith(">"):
            continue

        kept.append(line)

    # Remove trailing blank lines
    while kept and not kept[-1].strip():
        kept.pop()

    return "\n".join(kept).strip()


def _html_to_text(html: str) -> str:
    """
    Very lightweight HTML -> plain text conversion for email bodies.
    Good enough for feeding into an LLM.
    """
    # Remove script/style blocks
    html = re.sub(r"(?is)<(script|style).*?>.*?(</\1>)", "", html)
    # Drop tags
    text = re.sub(r"<[^>]+>", "", html)
    # Unescape a few common entities
    text = (
        text.replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
    )
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _decode_base64(data: str) -> str:
    """
    Gmail uses base64url encoding. This helper decodes safely.
    """
    if not data:
        return ""
    # Pad to correct length for b64 decoder
    missing = len(data) % 4
    if missing:
        data += "=" * (4 - missing)
    try:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _extract_body_from_payload(payload: Dict) -> str:
    """
    Walk a Gmail message payload and extract the best plain-text body.

    - Prefer text/plain parts
    - Fall back to text/html (converted to text)
    - Ignores attachments automatically (Gmail separates them)
    """
    plain_parts: List[str] = []
    html_parts: List[str] = []

    def walk(part: Dict):
        mime = (part.get("mimeType") or "").lower()
        body = part.get("body", {}) or {}

        data = body.get("data")
        if data:
            decoded = _decode_base64(data)
            if mime == "text/plain":
                plain_parts.append(decoded)
            elif mime == "text/html":
                html_parts.append(decoded)

        for child in part.get("parts", []) or []:
            walk(child)

    walk(payload)

    if plain_parts:
        return "\n".join(plain_parts).strip()
    if html_parts:
        return "\n".join(_html_to_text(h) for h in html_parts).strip()
    return ""


def _extract_attachments(payload: Dict) -> List[Dict[str, Any]]:
    """
    Walk a Gmail message payload and extract attachment metadata.
    
    Returns a list of dicts:
    {
        "filename": str,
        "mimeType": str,
        "size": int,
        "attachmentId": str
    }
    """
    attachments: List[Dict[str, Any]] = []
    
    def walk(part: Dict):
        body = part.get("body", {}) or {}
        filename = part.get("filename", "")
        attachment_id = body.get("attachmentId")
        
        # If there's an attachmentId and a filename, it's an attachment
        if attachment_id and filename:
            attachments.append({
                "filename": filename,
                "mimeType": part.get("mimeType", "application/octet-stream"),
                "size": body.get("size", 0),
                "attachmentId": attachment_id,
            })
        
        for child in part.get("parts", []) or []:
            walk(child)
    
    walk(payload)
    return attachments


def _get_file_icon(mime_type: str, filename: str) -> str:
    """Return an emoji icon based on file type."""
    mime_lower = mime_type.lower()
    filename_lower = filename.lower()
    
    if mime_lower.startswith("image/"):
        return "🖼️"
    elif mime_lower == "application/pdf" or filename_lower.endswith(".pdf"):
        return "📄"
    elif mime_lower.startswith("video/"):
        return "🎬"
    elif mime_lower.startswith("audio/"):
        return "🎵"
    elif "spreadsheet" in mime_lower or filename_lower.endswith((".xlsx", ".xls", ".csv")):
        return "📊"
    elif "document" in mime_lower or filename_lower.endswith((".doc", ".docx")):
        return "📝"
    elif "presentation" in mime_lower or filename_lower.endswith((".ppt", ".pptx")):
        return "📽️"
    elif "zip" in mime_lower or "compressed" in mime_lower or filename_lower.endswith((".zip", ".rar", ".7z")):
        return "🗜️"
    elif "text/" in mime_lower:
        return "📃"
    else:
        return "📎"


def download_attachment(message_id: str, attachment_id: str) -> bytes:
    """
    Download an attachment by message ID and attachment ID.
    
    Returns the raw bytes of the attachment.
    """
    global _gmail_service
    
    if _gmail_service is None:
        creds = get_creds()
        _gmail_service = build("gmail", "v1", credentials=creds)
    
    attachment = _gmail_service.users().messages().attachments().get(
        userId="me",
        messageId=message_id,
        id=attachment_id
    ).execute()
    
    data = attachment.get("data", "")
    # Pad for base64 decoding
    missing = len(data) % 4
    if missing:
        data += "=" * (4 - missing)
    
    return base64.urlsafe_b64decode(data)


# -------------------------------------------------------------------
# Main API
# -------------------------------------------------------------------

def fetch_recent_emails(limit: int = 20, unread_only: bool = False) -> List[Dict[str, Any]]:
    """
    Fetch recent emails via the Gmail HTTP API.

    Returns a list of dicts:
    {
        "id": ...,           # Gmail message ID (for attachment downloads)
        "from": ...,
        "subject": ...,
        "date": ...,
        "body": ...,         # reply-stripped plain text body
        "attachments": [     # list of attachment metadata
            {
                "filename": str,
                "mimeType": str,
                "size": int,
                "attachmentId": str,
                "icon": str   # emoji icon for the file type
            }
        ]
    }

    Args:
        limit: Max number of recent messages to return.
        unread_only: If True, only fetch messages matching is:unread.
    """
    global _gmail_service
    
    t0 = time.perf_counter()

    # --- Auth + service build ---
    creds = get_creds()
    t_auth = time.perf_counter()

    service = build("gmail", "v1", credentials=creds)
    _gmail_service = service  # Cache for attachment downloads
    t_service = time.perf_counter()

    # --- List message IDs ---
    query = "is:unread" if unread_only else None
    list_kwargs = {
        "userId": "me",
        "maxResults": limit,
        "labelIds": ["INBOX"],
    }
    if query:
        list_kwargs["q"] = query

    list_resp = service.users().messages().list(**list_kwargs).execute()
    t_list = time.perf_counter()

    messages = list_resp.get("messages", []) or []
    ids = [m["id"] for m in messages]

    if not ids:
        t_done = time.perf_counter()
        print(
            "[gmail_read] timing breakdown:\n"
            f"  AUTH:       {t_auth - t0:.3f}s\n"
            f"  SERVICE:    {t_service - t_auth:.3f}s\n"
            f"  LIST IDS:   {t_list - t_service:.3f}s\n"
            f"  FETCH MSGS: 0.000s (no messages)\n"
            f"  TOTAL:      {t_done - t0:.3f}s\n"
        )
        return []

    # --- Fetch each message (still fast over HTTP) ---
    emails: List[Dict[str, Any]] = []
    t_fetch_start = time.perf_counter()

    for mid in ids:
        msg = service.users().messages().get(
            userId="me",
            id=mid,
            format="full",
        ).execute()

        payload = msg.get("payload", {}) or {}
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

        from_ = _decode_header(headers.get("From", ""))
        subject = _decode_header(headers.get("Subject", ""))
        date = headers.get("Date", "")

        body_raw = _extract_body_from_payload(payload)
        body = strip_replies(body_raw)
        
        # Extract attachments with icons
        attachments = _extract_attachments(payload)
        for att in attachments:
            att["icon"] = _get_file_icon(att["mimeType"], att["filename"])

        emails.append(
            {
                "id": mid,
                "from": from_,
                "subject": subject,
                "date": date,
                "body": body,
                "attachments": attachments,
            }
        )

    t_fetch_end = time.perf_counter()
    t_done = time.perf_counter()

    print(
        "[gmail_read] timing breakdown:\n"
        f"  AUTH:       {t_auth - t0:.3f}s\n"
        f"  SERVICE:    {t_service - t_auth:.3f}s\n"
        f"  LIST IDS:   {t_list - t_service:.3f}s\n"
        f"  FETCH MSGS: {t_fetch_end - t_fetch_start:.3f}s for {len(ids)} msgs\n"
        f"  TOTAL:      {t_done - t0:.3f}s\n"
    )

    return emails


if __name__ == "__main__":
    # quick sanity check
    emails = fetch_recent_emails(limit=5, unread_only=False)
    for e in emails:
        print("ID:", e["id"])
        print("FROM:", e["from"])
        print("SUBJECT:", e["subject"])
        print("DATE:", e["date"])
        print("BODY PREVIEW:", e["body"].replace("\n", " ")[:200], "...")
        if e["attachments"]:
            print("ATTACHMENTS:")
            for att in e["attachments"]:
                print(f"  {att['icon']} {att['filename']} ({att['mimeType']}, {att['size']} bytes)")
        print("-" * 40)
