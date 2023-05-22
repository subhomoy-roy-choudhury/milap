from meet_api.meet import MeetAPI

event = MeetAPI(
    token_path="", 
    credentials_path="",
    date="2023-12-01",
    time="10:59",
    summary="summary",
    location="location",
    description="description"   
).meet()