import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError


class GoogleMeetService(object):
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self, client_id: str, client_secret: str, refresh_token: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token

    def _get_service(self) -> Optional[Resource]:
        try:
            # Construct credentials from stored information
            creds = Credentials.from_authorized_user_info(
                {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "token_uri": "https://oauth2.googleapis.com/token",
                },
                self.SCOPES,
            )

            # Refresh credentials if necessary
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())

            # Build the Google Calendar service
            return build("calendar", "v3", credentials=creds)
        except HttpError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except Exception as e:
            print(f"Error in getting Google Calendar service: {e}")
        return None

    @staticmethod
    def _prepare_utc_datetime_strings(date_str: str, time_str: str) -> tuple[str, str]:
        try:
            # Combine date and time strings and parse them into datetime objects
            datetime_format = "%Y-%m-%dT%H:%M:%S"
            start_datetime_str = f"{date_str}T{time_str}:00"
            end_datetime_str = f"{date_str}T{time_str}:45"

            start_datetime = datetime.strptime(start_datetime_str, datetime_format)
            end_datetime = datetime.strptime(end_datetime_str, datetime_format)

            # Convert to UTC and format to ISO 8601
            start_utc = start_datetime.astimezone(timezone.utc).isoformat(
                timespec="milliseconds"
            )
            end_utc = end_datetime.astimezone(timezone.utc).isoformat(
                timespec="milliseconds"
            )

            return start_utc, end_utc
        except ValueError as e:
            print(f"Error in processing date and time strings: {e}")
            return None, None

    def _insert_calendar_event(
        self, service: Resource, date: str, time: str, summary: str, description: str
    ) -> Optional[dict]:
        start_utc, end_utc = self._prepare_utc_datetime_strings(date, time)
        if not start_utc or not end_utc:
            print("Invalid start or end UTC time.")
            return None

        event = {
            "summary": summary,
            "description": description,
            "colorId": 1,
            "conferenceData": {
                "createRequest": {
                    "requestId": str(uuid.uuid4()),  # Unique request ID for each event
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
            "start": {"dateTime": start_utc, "timeZone": "UTC"},
            "end": {"dateTime": end_utc, "timeZone": "UTC"},
        }

        try:
            inserted_event = (
                service.events()
                .insert(
                    calendarId="primary",
                    sendNotifications=True,
                    body=event,
                    conferenceDataVersion=1,
                )
                .execute()
            )

            return inserted_event
        except HttpError as error:
            print(f"Error in inserting calendar event: {error}")
            return None

    def is_slot_booked(self, date: str, time: str, organizer_email: str) -> bool:
        service: Optional[Resource] = self._get_service()
        if service is None:
            return False

        start_utc, end_utc = self._prepare_utc_datetime_strings(date, time)
        if not start_utc or not end_utc:
            return False

        try:
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=start_utc,
                    timeMax=end_utc,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            return any(
                event.get("organizer", {}).get("email") == organizer_email
                for event in events_result.get("items", [])
            )
        except HttpError as error:
            print(f"Error in fetching events: {error}")
            return False

    def create_meeting_event(
        self, date: str, time: str, summary: str, description: str
    ) -> Optional[dict]:
        service: Optional[Resource] = self._get_service()
        if service is None:
            return None

        return self._insert_calendar_event(service, date, time, summary, description)

    def update_meeting_event(
        self, event_id: str, updated_data: Dict[str, any]
    ) -> Optional[Dict]:
        service: Optional[Resource] = self._get_service()
        if service is None:
            return None

        try:
            event = (
                service.events().get(calendarId="primary", eventId=event_id).execute()
            )

            event.update(updated_data)
            updated_event = (
                service.events()
                .update(calendarId="primary", eventId=event_id, body=event)
                .execute()
            )
            return updated_event
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    def delete_meeting_event(self, event_id: str) -> bool:
        service: Optional[Resource] = self._get_service()
        if service is None:
            return False

        try:
            service.events().delete(calendarId="primary", eventId=event_id).execute()
            return True
        except HttpError as error:
            print(f"An error occurred: {error}")
            return False

    def fetch_meeting_by_criteria(
        self, time_min: str, time_max: str, query: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        service: Optional[Resource] = self._get_service()
        if service is None:
            return None

        try:
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    q=query,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            return events_result.get("items", [])
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
