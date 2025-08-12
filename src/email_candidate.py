import os.path
import base64
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- CONFIGURATION ---
# Change the scope to the Gmail API's 'send' scope
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json' # This will be created after the first run

def get_credentials():
    """Handles user authentication and token management for the Gmail API."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # If you change SCOPES, the old token.json might not work.
            # It's best to delete token.json if you have issues.
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds

def send_email(recipient, sender, subject, body):
    """
    Creates and sends an email using the Gmail API.

    Args:
        recipient (str): The recipient's email address.
        subject (str): The subject of the email.
        body (str): The plain text body of the email.
    """
    try:
        creds = get_credentials()
        service = build("gmail", "v1", credentials=creds)

        # Create the email message object
        message = EmailMessage()
        message.set_content(body)
        message["To"] = recipient
        message["From"] = sender  
        message["Subject"] = subject

        # Encode the message in base64url format
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"raw": encoded_message}

        # Call the Gmail API to send the message
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        print(f"✅ Email sent successfully! Message ID: {send_message['id']}")

    except HttpError as error:
        print(f"❌ An error occurred: {error}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")