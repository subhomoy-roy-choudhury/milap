import datetime
from datetime import datetime, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleMeetService(object):
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self, client_id: str, client_secret: str, refresh_token: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token

    @staticmethod
    def _prepare_utc_datetime_strings(date_str, time_str):
        hour = time_str.split(":")[0]
        date1 = f"{date_str}T{hour}:00:30"
        date2 = f"{date_str}T{hour}:45:30"
        x = datetime.strptime(date1, "%Y-%m-%dT%H:%M:%S")
        y = datetime.strptime(date2, "%Y-%m-%dT%H:%M:%S")
        x_utc = x.astimezone(timezone.utc)
        y_utc = y.astimezone(timezone.utc)
        return x_utc.strftime("%Y-%m-%dT%H:%M:00.000Z"), y_utc.strftime(
            "%Y-%m-%dT%H:%M:00.000Z"
        )

    def _insert_calendar_event(self, service, date, time, summary, description):
        start_utc, end_utc = self._prepare_utc_datetime_strings(date, time)
        event = {
            "summary": summary,
            "description": description,
            "colorId": 1,
            "conferenceData": {
                "createRequest": {
                    "requestId": "zz",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
            "start": {"dateTime": start_utc, "timeZone": "UTC"},
            "end": {"dateTime": end_utc, "timeZone": "UTC"},
        }
        return (
            service.events()
            .insert(
                calendarId="primary",
                sendNotifications=True,
                body=event,
                conferenceDataVersion=1,
            )
            .execute()
        )

    def create_meeting_event(self, date, time, summary, description):
        creds = Credentials.from_authorized_user_info(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "token_uri": "https://oauth2.googleapis.com/token",
            },
            self.SCOPES,
        )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print("Invalid credentials.")
                return None

        try:
            service = build("calendar", "v3", credentials=creds)
            return self._insert_calendar_event(service, date, time, summary, description)
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
