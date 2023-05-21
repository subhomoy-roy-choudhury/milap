from __future__ import print_function

import uuid
import datetime
from datetime import datetime, timedelta, timezone
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
# Reading Data from Google API
# SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
# CRUD Operations in Google API
SCOPES = ["https://www.googleapis.com/auth/calendar"]

class MeetAPI(object):
    def __init__(self,token_path, credentials_path, date, time, summary, location, description):
        self.token_path = token_path
        self.credentials_path = credentials_path
        self.date = date
        self.time = time
        self.summary = summary
        self.location = location
        self.description = description
    
    
    def meet(self):
        """Shows basic usage of the Google Calendar API.
        Prints the start and name of the next 10 events on the user's calendar.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        
        token_file = os.path.join(self.token_path, "token.json")
        credentials_file = os.path.join(self.token_path, "credentials.json")
        
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_file, "w", encoding="utf8") as token:
                token.write(creds.to_json())

        try:
            # Date Manipulation
            # date1 = self.date + "T" + self.time.split(":")[0] + ":00" + ":30"
            # date2 = self.date + "T" + self.time.split(":")[0] + ":45" + ":30"

            # x = datetime.strptime(self.date + "T" + self.time.split(":")[0] + ":00" + ":30", "%Y-%m-%dT%H:%M:%S")
            # x_utc = x.astimezone(timezone.utc)
            # y = datetime.strptime(self.date + "T" + self.time.split(":")[0] + ":45" + ":30", "%Y-%m-%dT%H:%M:%S")
            # y_utc = y.astimezone(timezone.utc)

            # end1 = self.date + "T" + str(x_utc.hour) + ":" + str(x_utc.minute) + ":00" + ".000Z"
            # end2 = self.date + "T" + str(y_utc.hour) + ":" + str(y_utc.minute) + ":00" + ".000Z"
            
            # Extract the hour component from self.time
            hour = self.time.split(":")[0]

            # Format the date and time strings
            date1 = f"{self.date}T{hour}:00:30"
            date2 = f"{self.date}T{hour}:45:30"

            # Create datetime objects in local time
            x = datetime.strptime(date1, "%Y-%m-%dT%H:%M:%S")
            y = datetime.strptime(date2, "%Y-%m-%dT%H:%M:%S")

            # Convert datetime objects to UTC
            x_utc = x.astimezone(timezone.utc)
            y_utc = y.astimezone(timezone.utc)

            # Format the UTC datetime strings
            end1 = x_utc.strftime("%Y-%m-%dT%H:%M:00.000Z")
            end2 = y_utc.strftime("%Y-%m-%dT%H:%M:00.000Z")

            
            # Create a new calender instance.
            service = build("calendar", "v3", credentials=creds)
            
            
            # Call the Calendar API

            # checking whether teacher is busy or not
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=end1,
                    timeMax=end2,
                    maxResults=1,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            if events:
                print("you are busy for this time slot !")
                return None

            # Create Google Calender Event
            
            # Create a new event start date instance for teacher in their calendar.
            # event_start_time = datetime.now()
            # event_start_time.day = int(self.date.split("-")[2])

            # event_end_time = datetime.now()
            # event_end_time.day = int(self.date.split("-")[2])
            # event_end_time += timedelta(minutes=45)
            
            event = {
                "summary": f"{self.summary}",
                "description": f"{self.description}",
                "colorId": 1,
                "conferenceData": {
                    "createRequest": {
                        "requestId": "zz",
                        "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    }
                },
                "start": {"dateTime": date1, "timeZone": "Asia/Kolkata"},
                "end": {"dateTime": date2, "timeZone": "Asia/Kolkata"},
            }

            event_result = (
                service.events()
                .insert(
                    calendarId="primary",
                    sendNotifications=True,
                    body=event,
                    conferenceDataVersion=1,
                )
                .execute()
            )
            
            return event_result

        except HttpError as error:
            print("An error occurred: %s" % error)


if __name__ == "__main__":
    event = MeetAPI(
        token_path="", 
        credentials_path="",
        date="2023-12-01",
        time="10:59",
        summary="summary",
        location="location",
        description="description"   
    ).meet()