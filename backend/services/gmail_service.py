import base64
import os
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Optional, Dict, Any
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH, GMAIL_SCOPES
from models.schemas import Email, EmailAttachment, EmailReply, ComposeEmail


class GmailService:
    def __init__(self):
        self.service = None
        self.user_email = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API."""
        creds = None

        if os.path.exists(GMAIL_TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, GMAIL_SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    creds = None

            if not creds:
                flow = InstalledAppFlow.from_client_secrets_file(
                    GMAIL_CREDENTIALS_PATH, GMAIL_SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(GMAIL_TOKEN_PATH, "w") as token:
                token.write(creds.to_json())

        self.service = build("gmail", "v1", credentials=creds)

        # Get user email
        profile = self.service.users().getProfile(userId="me").execute()
        self.user_email = profile.get("emailAddress")

    def get_unread_emails(self, max_results: int = 50) -> List[Email]:
        """Fetch unread emails from inbox."""
        try:
            results = self.service.users().messages().list(
                userId="me",
                labelIds=["INBOX", "UNREAD"],
                maxResults=max_results
            ).execute()

            messages = results.get("messages", [])
            emails = []

            for msg in messages:
                email = self._get_email_details(msg["id"])
                if email:
                    emails.append(email)

            return emails

        except HttpError as error:
            print(f"Error fetching emails: {error}")
            return []

    def _get_email_details(self, message_id: str) -> Optional[Email]:
        """Get full details of an email."""
        try:
            message = self.service.users().messages().get(
                userId="me",
                id=message_id,
                format="full"
            ).execute()

            headers = message.get("payload", {}).get("headers", [])
            header_dict = {h["name"].lower(): h["value"] for h in headers}

            # Extract sender info
            sender = header_dict.get("from", "")
            sender_name = None
            if "<" in sender:
                match = re.match(r"(.+?)\s*<(.+?)>", sender)
                if match:
                    sender_name = match.group(1).strip().strip('"')
                    sender = match.group(2)

            # Extract body and attachments
            body, body_html, attachments = self._extract_body_and_attachments(
                message.get("payload", {}), message_id
            )

            # Parse date
            internal_date = int(message.get("internalDate", 0)) / 1000
            received_at = datetime.fromtimestamp(internal_date)

            return Email(
                id=message_id,
                thread_id=message.get("threadId", ""),
                sender=sender,
                sender_name=sender_name,
                recipient=self.user_email,
                subject=header_dict.get("subject", "(No Subject)"),
                body=body,
                body_html=body_html,
                attachments=attachments,
                received_at=received_at
            )

        except HttpError as error:
            print(f"Error getting email details: {error}")
            return None

    def _extract_body_and_attachments(
        self, payload: Dict[str, Any], message_id: str
    ) -> tuple:
        """Extract body text and attachments from email payload."""
        body = ""
        body_html = ""
        attachments = []

        def process_part(part):
            nonlocal body, body_html, attachments

            mime_type = part.get("mimeType", "")
            filename = part.get("filename", "")

            if filename and part.get("body", {}).get("attachmentId"):
                # This is an attachment
                attachment_id = part["body"]["attachmentId"]
                attachment_data = self.service.users().messages().attachments().get(
                    userId="me",
                    messageId=message_id,
                    id=attachment_id
                ).execute()

                attachments.append(EmailAttachment(
                    filename=filename,
                    mime_type=mime_type,
                    size=part["body"].get("size", 0),
                    content=attachment_data.get("data", "")
                ))
            elif mime_type == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            elif mime_type == "text/html":
                data = part.get("body", {}).get("data", "")
                if data:
                    body_html = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            elif "parts" in part:
                for sub_part in part["parts"]:
                    process_part(sub_part)

        # Handle single-part messages
        if "body" in payload and payload.get("body", {}).get("data"):
            data = payload["body"]["data"]
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        # Handle multi-part messages
        if "parts" in payload:
            for part in payload["parts"]:
                process_part(part)

        # Fall back to HTML if no plain text
        if not body and body_html:
            # Simple HTML to text conversion
            body = re.sub(r"<[^>]+>", "", body_html)
            body = body.replace("&nbsp;", " ").replace("&amp;", "&")

        return body.strip(), body_html, attachments

    def send_email(self, reply: EmailReply) -> Optional[str]:
        """Send an email with optional HTML body."""
        try:
            message = MIMEMultipart("alternative")
            message["To"] = reply.to
            message["From"] = self.user_email
            message["Subject"] = reply.subject

            # Add plain text body
            text_part = MIMEText(reply.body, "plain")
            message.attach(text_part)

            # Add HTML body if provided
            if reply.body_html:
                html_part = MIMEText(reply.body_html, "html")
                message.attach(html_part)

            # Encode and send
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {"raw": encoded_message}

            # If replying to a thread
            if reply.thread_id:
                create_message["threadId"] = reply.thread_id

            sent_message = self.service.users().messages().send(
                userId="me",
                body=create_message
            ).execute()

            return sent_message.get("id")

        except HttpError as error:
            print(f"Error sending email: {error}")
            return None

    def reply_to_email(self, original_email: Email, response_body: str) -> Optional[str]:
        """Reply to an existing email thread."""
        # Prepare reply subject
        subject = original_email.subject
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        reply = EmailReply(
            to=original_email.sender,
            subject=subject,
            body=response_body,
            thread_id=original_email.thread_id
        )

        return self.send_email(reply)

    def send_composed_email(self, compose: ComposeEmail) -> Optional[str]:
        """Send a composed email with CC/BCC support and optional HTML."""
        try:
            message = MIMEMultipart("alternative")
            message["From"] = self.user_email
            message["To"] = ", ".join(compose.to)
            message["Subject"] = compose.subject

            if compose.cc:
                message["Cc"] = ", ".join(compose.cc)

            if compose.bcc:
                message["Bcc"] = ", ".join(compose.bcc)

            # Add plain text body
            text_part = MIMEText(compose.body, "plain")
            message.attach(text_part)

            # Add HTML body if provided
            if compose.body_html:
                html_part = MIMEText(compose.body_html, "html")
                message.attach(html_part)

            # Encode and send
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {"raw": encoded_message}

            sent_message = self.service.users().messages().send(
                userId="me",
                body=create_message
            ).execute()

            return sent_message.get("id")

        except HttpError as error:
            print(f"Error sending composed email: {error}")
            return None

    def create_draft(self, reply: EmailReply) -> Optional[str]:
        """Create a draft email with optional HTML body."""
        try:
            message = MIMEMultipart("alternative")
            message["To"] = reply.to
            message["From"] = self.user_email
            message["Subject"] = reply.subject

            text_part = MIMEText(reply.body, "plain")
            message.attach(text_part)

            if reply.body_html:
                html_part = MIMEText(reply.body_html, "html")
                message.attach(html_part)

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            draft_body = {
                "message": {
                    "raw": encoded_message
                }
            }

            if reply.thread_id:
                draft_body["message"]["threadId"] = reply.thread_id

            draft = self.service.users().drafts().create(
                userId="me",
                body=draft_body
            ).execute()

            return draft.get("id")

        except HttpError as error:
            print(f"Error creating draft: {error}")
            return None

    def send_draft(self, draft_id: str) -> Optional[str]:
        """Send a previously created draft."""
        try:
            sent_message = self.service.users().drafts().send(
                userId="me",
                body={"id": draft_id}
            ).execute()

            return sent_message.get("id")

        except HttpError as error:
            print(f"Error sending draft: {error}")
            return None

    def delete_draft(self, draft_id: str) -> bool:
        """Delete a draft."""
        try:
            self.service.users().drafts().delete(
                userId="me",
                id=draft_id
            ).execute()
            return True
        except HttpError as error:
            print(f"Error deleting draft: {error}")
            return False

    def mark_as_read(self, message_id: str) -> bool:
        """Mark an email as read."""
        try:
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            return True
        except HttpError as error:
            print(f"Error marking as read: {error}")
            return False

    def get_attachment_content(self, message_id: str, attachment_id: str) -> Optional[bytes]:
        """Download attachment content."""
        try:
            attachment = self.service.users().messages().attachments().get(
                userId="me",
                messageId=message_id,
                id=attachment_id
            ).execute()

            data = attachment.get("data", "")
            return base64.urlsafe_b64decode(data)

        except HttpError as error:
            print(f"Error getting attachment: {error}")
            return None


# Singleton instance
_gmail_service: Optional[GmailService] = None


def get_gmail_service() -> GmailService:
    """Get or create Gmail service instance."""
    global _gmail_service
    if _gmail_service is None:
        _gmail_service = GmailService()
    return _gmail_service
