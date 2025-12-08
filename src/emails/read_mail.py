import imaplib
import ssl
from email import message_from_bytes
from email.header import decode_header, make_header

from .auth import get_creds

EMAIL = "ygarcia@g.hmc.edu"   # <- your address
IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993


def _decode_header(value: str) -> str:
    if not value:
        return ""
    return str(make_header(decode_header(value)))


def _get_body(msg) -> str:
    # Prefer text/plain parts
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "").lower()
            if ctype == "text/plain" and "attachment" not in disp:
                try:
                    charset = part.get_content_charset() or "utf-8"
                    return part.get_payload(decode=True).decode(charset, errors="replace")
                except Exception:
                    continue
        return ""
    else:
        try:
            charset = msg.get_content_charset() or "utf-8"
            return msg.get_payload(decode=True).decode(charset, errors="replace")
        except Exception:
            return ""


def fetch_recent_emails(limit: int = 20):
    """
    Return a list of the most recent emails as dicts:
    {
        "from": ...,
        "subject": ...,
        "date": ...,
        "body": ...
    }
    """
    creds = get_creds()
    access_token = creds.token

    auth_string = f"user={EMAIL}\1auth=Bearer {access_token}\1\1"

    context = ssl.create_default_context()
    imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=context)
    imap.authenticate("XOAUTH2", lambda _: auth_string.encode("utf-8"))

    imap.select("INBOX")

    # You can switch "ALL" to "UNSEEN" if you only want unread
    typ, data = imap.search(None, "ALL")
    if typ != "OK":
        imap.logout()
        return []

    ids = data[0].split()
    ids = ids[-limit:]  # most recent N

    emails = []
    for msg_id in ids:
        typ, msg_data = imap.fetch(msg_id, "(BODY.PEEK[])") 
        if typ != "OK":
            continue

        raw = msg_data[0][1]
        msg = message_from_bytes(raw)

        from_ = _decode_header(msg.get("From", ""))
        subject = _decode_header(msg.get("Subject", ""))
        date = msg.get("Date", "")
        body = _get_body(msg)

        emails.append(
            {
                "from": from_,
                "subject": subject,
                "date": date,
                "body": body,
            }
        )

    imap.logout()
    return emails


if __name__ == "__main__":
    # quick sanity check
    for e in fetch_recent_emails(5):
        print("FROM:", e["from"])
        print("SUBJECT:", e["subject"])
        print("DATE:", e["date"])
        print("BODY PREVIEW:", e["body"].replace("\n", " "), "...")
        print("-" * 40)
