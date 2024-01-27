from meet_api.main import GoogleMeetService
from datetime import datetime

google_meet_service = GoogleMeetService(
    client_id="129906636160-go0nig6got2r9bqj4q4s9g42ghn0c9j8.apps.googleusercontent.com",
    client_secret="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",
    refresh_token="1//0g2uO1vefKJubCgYIARAAGBASNwF-L9IrPqiZ5rIlBwo92ZmDy4AJY9kZ21ZPzH9eBVwVkKpajonPFqak8coWVaWx23GdfSog5rc",
)

# Create Meeting
event_details = google_meet_service.create_meeting_event(
    date="2023-12-01",
    time="10:59",
    summary="summary",
    description="description",
)

# Fetch Meetings
events_list = google_meet_service.fetch_meeting_by_criteria(
    time_min="2022-01-01T00:00:00Z", time_max="2022-01-02T00:00:00Z", query="meeting"
)

# Update Meeting
updated_meeting_details = google_meet_service.update_meeting_event(
    event_id=event_details["id"], updated_data={"summary": "Updated Meeting"}
)

# Delete Meeting
deleted_meeting_details = google_meet_service.delete_meeting_event(
    event_id=event_details["id"]
)

print("Sample Execution Completed ..")
