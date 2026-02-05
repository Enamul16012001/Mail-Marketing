import base64
import os.path
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://mail.google.com/"]

def authenticate_gmail():
    """
    Handles authentication with the Gmail API.
    Returns:
        creds (google.oauth2.credentials.Credentials): The authenticated credentials.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                # Optional: Delete corrupted token file to force re-login
                # os.remove("token.json")
                return None
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
            
    return creds

def gmail_send_message():
    """Create and send an email message using the shared auth function."""
    
    # 1. Get credentials from our new helper function
    creds = authenticate_gmail()
    
    if not creds:
        print("Failed to retrieve credentials.")
        return

    try:
        service = build("gmail", "v1", credentials=creds)
        message = EmailMessage()

        message.set_content("Yes I can send email by gmail API")

        # distinct emails for testing
        message["To"] = "recipient@example.com" 
        message["From"] = "sender@example.com"
        message["Subject"] = "Testing Gmail API"

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"raw": encoded_message}
        
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        print(f'Message Id: {send_message["id"]}')
        return send_message

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

if __name__ == "__main__":
  gmail_send_message()