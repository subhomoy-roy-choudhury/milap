from milap import GoogleMeetService

google_meet_service = GoogleMeetService(
    client_id="<GOOGLE CLOUD CLIENT ID>",
    client_secret="<GOOGLE CLOUD CLIENT SECRET>",
    refresh_token="<REFRESH TOEKN>",
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
