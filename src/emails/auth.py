from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Full Gmail/IMAP access
SCOPES = ["https://mail.google.com/"]

# Paths relative to this file (src/emails/)
BASE_DIR = Path(__file__).resolve().parent
CLIENT_SECRETS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"


def get_creds() -> Credentials:
    """
    Return valid Google OAuth2 credentials for Gmail/IMAP.

    - Reads client ID/secret from credentials.json (downloaded from Google Cloud).
    - Stores access + refresh tokens in token.json.
    - Refreshes tokens automatically when expired.
    - Uses a local web server OAuth flow (browser opens, redirect to localhost).
    """
    creds: Credentials | None = None

    # Load existing token if present
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # If no valid creds, either refresh or do full OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Silent refresh using the refresh token
            creds.refresh(Request())
        else:
            if not CLIENT_SECRETS_FILE.exists():
                raise FileNotFoundError(
                    f"Could not find {CLIENT_SECRETS_FILE}. "
                    f"Make sure credentials.json is in {BASE_DIR}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRETS_FILE), SCOPES
            )

            # This opens a browser tab, you log in + Duo + Allow,
            # then Google redirects back to localhost and the script continues.
            creds = flow.run_local_server(
                host="localhost",
                port=0,
                open_browser=True,
            )

        # Save (new or refreshed) credentials
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return creds
