import datetime
import os.path
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- CONFIGURATION ---
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TIMEZONE = 'Asia/Kolkata'
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'


def get_credentials():
    """Handles user authentication and token management."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds


class MeetingScheduler:
    """
    A class to schedule a Google Meet event.

    Attributes:
        summary (str): The title of the meeting.
        description (str): The meeting's description.
        start_time (datetime): The start time of the meeting.
        end_time (datetime): The end time of the meeting.
        attendees (list): A list of attendee email addresses.
    """
    def __init__(self, summary, description, start_time, end_time, attendees):
        self.summary = summary
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.attendees = attendees
        self.creds = get_credentials()
        self.service = build("calendar", "v3", credentials=self.creds)

    def _build_event_body(self):
        """Constructs the event dictionary for the Google Calendar API."""
        attendee_list = [{"email": email} for email in self.attendees]
        event = {
            "summary": self.summary,
            "description": self.description,
            "start": {
                "dateTime": self.start_time.isoformat(),
                "timeZone": TIMEZONE,
            },
            "end": {
                "dateTime": self.end_time.isoformat(),
                "timeZone": TIMEZONE,
            },
            "attendees": attendee_list,
            "conferenceData": {
                "createRequest": {
                    "requestId": f"{datetime.datetime.now().timestamp()}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},
                    {"method": "popup", "minutes": 15},
                ],
            },
        }
        return event

    def schedule(self):
        """
        Calls the Google Calendar API to create the event and send invitations.
        Returns the created event object on success, or None on failure.
        """
        event_body = self._build_event_body()
        try:
            created_event = (
                self.service.events()
                .insert(
                    calendarId="primary",
                    body=event_body,
                    sendNotifications=True,
                    conferenceDataVersion=1,
                )
                .execute()
            )
            print("\n✅ Success! Meeting scheduled.")
            print(f"🔗 Google Meet Link: {created_event.get('hangoutLink')}")
            print(f"📅 View on Google Calendar: {created_event.get('htmlLink')}")
            return created_event
        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return None