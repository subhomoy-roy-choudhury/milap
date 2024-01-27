from meet_api.main import GoogleMeetService

google_meet_service = GoogleMeetService(
    client_id="129906636160-go0nig6got2r9bqj4q4s9g42ghn0c9j8.apps.googleusercontent.com",
    client_secret="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",
    refresh_token="1//0geMQTWBdZ1LpCgYIARAAGBASNwF-L9IrQg-75gVKCOYel6mteDrLG2QWD5NuIH6JCzdZDeDjvZCa4nM26vUTzWNv5P29j2xVE3o",
)
event_details = google_meet_service.create_meeting_event(
    date="2023-12-01",
    time="10:59",
    summary="summary",
    description="description",
)
