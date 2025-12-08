import re
import ssl
import imaplib
from typing import List, Dict, Optional
from email import message_from_bytes
from email.header import decode_header, make_header

from .auth import get_creds


EMAIL = "ygarcia@g.hmc.edu"   # <- your address
IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993


def _decode_header(value: Optional[str]) -> str:
    """
    Safely decode MIME-encoded headers (e.g., subject, from).
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


def _get_body(msg) -> str:
    """
    Extract the best plain-text body from an email.message.Message.

    - Prefer text/plain parts
    - Fall back to text/html (converted to text)
    - Ignore attachments and images
    """
    if msg.is_multipart():
        plain_parts: List[str] = []
        html_parts: List[str] = []

        for part in msg.walk():
            ctype = (part.get_content_type() or "").lower()
            disp = (part.get("Content-Disposition") or "").lower()

            # Skip attachments and inline images
            if "attachment" in disp or ctype.startswith("image/") or ctype.startswith("application/"):
                continue

            try:
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
            except Exception:
                continue

            if ctype == "text/plain":
                plain_parts.append(text)
            elif ctype == "text/html":
                html_parts.append(text)

        if plain_parts:
            return "\n".join(plain_parts).strip()
        if html_parts:
            return "\n".join(_html_to_text(h) for h in html_parts).strip()
        return ""
    else:
        # Single-part message
        try:
            payload = msg.get_payload(decode=True) or b""
            charset = msg.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
        except Exception:
            text = msg.get_payload() or ""

        ctype = (msg.get_content_type() or "").lower()
        if ctype == "text/html" or "<html" in text.lower():
            return _html_to_text(text)
        return text.strip()


def fetch_recent_emails(limit: int = 20, unread_only: bool = False) -> List[Dict[str, str]]:
    """
    Return a list of the most recent emails as dicts:
    {
        "from": ...,
        "subject": ...,
        "date": ...,
        "body": ...   # reply-stripped plain-text body
    }

    Args:
        limit: Max number of recent messages to return.
        unread_only: If True, only fetch UNSEEN messages; otherwise ALL.
    """
    creds = get_creds()
    access_token = creds.token

    # XOAUTH2 auth string for Gmail IMAP
    auth_string = f"user={EMAIL}\1auth=Bearer {access_token}\1\1"

    context = ssl.create_default_context()
    imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=context)
    imap.authenticate("XOAUTH2", lambda _: auth_string.encode("utf-8"))

    try:
        imap.select("INBOX")

        search_criteria = "UNSEEN" if unread_only else "ALL"
        typ, data = imap.search(None, search_criteria)
        if typ != "OK":
            return []

        ids = data[0].split()
        if not ids:
            return []

        # Take only the most recent N
        ids = ids[-limit:]

        emails: List[Dict[str, str]] = []

        for msg_id in ids:
            typ, msg_data = imap.fetch(msg_id, "(BODY.PEEK[])")
            if typ != "OK" or not msg_data or not isinstance(msg_data[0], tuple):
                continue

            raw = msg_data[0][1]
            if not raw:
                continue

            msg = message_from_bytes(raw)

            from_ = _decode_header(msg.get("From", ""))
            subject = _decode_header(msg.get("Subject", ""))
            date = msg.get("Date", "")

            body_raw = _get_body(msg)
            body = strip_replies(body_raw)

            emails.append(
                {
                    "from": from_,
                    "subject": subject,
                    "date": date,
                    "body": body,
                }
            )

        return emails

    finally:
        try:
            imap.close()
        except Exception:
            pass
        imap.logout()


if __name__ == "__main__":
    # quick sanity check
    for e in fetch_recent_emails(limit=5, unread_only=False):
        print("FROM:", e["from"])
        print("SUBJECT:", e["subject"])
        print("DATE:", e["date"])
        print("BODY PREVIEW:", e["body"].replace("\n", " ")[:300], "...")
        print("-" * 40)
