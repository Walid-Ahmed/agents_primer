"""Local MCP server exposing Gmail draft and send actions.

``send_draft`` really sends email. The client places a human approval check in
front of that call.
"""

import base64
import os
from email import policy
from email.parser import BytesParser
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("gmail-tools")
# Read mail plus create/send drafts. These are still narrower than the broad
# https://mail.google.com/ scope.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]
ROOT = Path(__file__).resolve().parents[1]
CREDENTIALS_FILE = Path(os.getenv("GMAIL_CREDENTIALS_FILE", ROOT / "credentials.json"))
TOKEN_FILE = Path(os.getenv("GMAIL_TOKEN_FILE", ROOT / "token.json"))


def gmail_service():
    """Authenticate the user and return a Gmail API client."""
    credentials = None
    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    elif not credentials or not credentials.valid or not credentials.has_scopes(SCOPES):
        if not CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                f"Missing {CREDENTIALS_FILE}. Follow mcp_examples/GMAIL_README.md."
            )
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        credentials = flow.run_local_server(port=0)

    TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=credentials)


def header(message: dict, name: str) -> str:
    """Read one header from a Gmail API message resource."""
    headers = message.get("payload", {}).get("headers", [])
    return next((item["value"] for item in headers if item["name"].lower() == name), "")


def decode_message(message: dict) -> dict:
    """Decode a Gmail raw message into the fields useful to this lesson."""
    raw = base64.urlsafe_b64decode(message["raw"] + "===")
    parsed = BytesParser(policy=policy.default).parsebytes(raw)
    body = parsed.get_body(preferencelist=("plain",))
    return {
        "message_id": message["id"],
        "from": str(parsed.get("From", "")),
        "to": str(parsed.get("To", "")),
        "subject": str(parsed.get("Subject", "")),
        "date": str(parsed.get("Date", "")),
        "body": (body.get_content() if body else parsed.get_content())[:12000],
    }


@mcp.tool()
def search_emails(query: str = "newer_than:7d", max_results: int = 5) -> list[dict]:
    """Search Gmail using Gmail query syntax and return matching thread summaries."""
    max_results = max(1, min(max_results, 10))
    service = gmail_service()
    matches = (
        service.users()
        .threads()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
        .get("threads", [])
    )
    results = []
    for match in matches:
        thread = (
            service.users()
            .threads()
            .get(
                userId="me",
                id=match["id"],
                format="metadata",
                metadataHeaders=["From", "To", "Subject", "Date"],
            )
            .execute()
        )
        latest = thread["messages"][-1]
        results.append(
            {
                "thread_id": thread["id"],
                "from": header(latest, "from"),
                "to": header(latest, "to"),
                "subject": header(latest, "subject"),
                "date": header(latest, "date"),
                "snippet": latest.get("snippet", ""),
            }
        )
    return results


@mcp.tool()
def read_thread(thread_id: str) -> list[dict]:
    """Read every message in one Gmail thread, including its plain-text body."""
    thread = (
        gmail_service()
        .users()
        .threads()
        .get(userId="me", id=thread_id, format="raw")
        .execute()
    )
    return [decode_message(message) for message in thread["messages"]]


@mcp.tool()
def create_draft(to: str, subject: str, body: str) -> dict:
    """Create a Gmail draft. This does not send the email."""
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    draft = (
        gmail_service()
        .users()
        .drafts()
        .create(userId="me", body={"message": {"raw": raw}})
        .execute()
    )
    return {"draft_id": draft["id"], "to": to, "subject": subject, "body": body}


@mcp.tool()
def send_draft(draft_id: str) -> dict:
    """Send an existing Gmail draft. This is an irreversible external action."""
    sent = (
        gmail_service()
        .users()
        .drafts()
        .send(userId="me", body={"id": draft_id})
        .execute()
    )
    return {"sent": True, "message_id": sent["id"]}


if __name__ == "__main__":
    mcp.run(transport="stdio")
