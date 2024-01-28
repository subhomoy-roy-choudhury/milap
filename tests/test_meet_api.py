import pytest
from unittest.mock import Mock, patch
from googleapiclient.errors import HttpError
from datetime import datetime
from dateutil import parser
from src.milap.main import GoogleMeetService


# Test for successful service creation
@patch("src.milap.main.build")
@patch("src.milap.main.Credentials.from_authorized_user_info")
def test_get_service_success(mock_credentials, mock_build):
    mock_credentials.return_value = Mock(expired=False)
    mock_build.return_value = Mock()

    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    service = gms._get_service()

    mock_credentials.assert_called_once()
    mock_build.assert_called_once()
    assert service is not None


# Test for failure due to HTTP error
@patch("src.milap.main.build", side_effect=HttpError(Mock(status=404), b"Not found"))
@patch("src.milap.main.Credentials.from_authorized_user_info")
def test_get_service_http_error(mock_credentials, mock_build):
    mock_credentials.return_value = Mock(expired=False)

    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    service = gms._get_service()

    assert service is None


# Test for failure due to other exceptions
@patch("src.milap.main.build", side_effect=Exception("Random error"))
@patch("src.milap.main.Credentials.from_authorized_user_info")
def test_get_service_other_exception(mock_credentials, mock_build):
    mock_credentials.return_value = Mock(expired=False)

    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    service = gms._get_service()

    assert service is None


@pytest.mark.parametrize(
    "date_str, time_str, expected_start, expected_end",
    [
        (
            "2022-01-01",
            "12:00",
            "2022-01-01T06:30:00.000+00:00",
            "2022-01-01T06:30:45.000+00:00",
        ),  # Valid datetime
        (
            "2022-12-31",
            "23:00",
            "2022-12-31T17:30:00.000+00:00",
            "2022-12-31T17:30:45.000+00:00",
        ),  # Edge case for day change
        # Add more test cases with valid inputs
    ],
)
def test_prepare_utc_datetime_strings_valid(
    date_str, time_str, expected_start, expected_end
):
    start_utc, end_utc = GoogleMeetService._prepare_utc_datetime_strings(
        date_str, time_str
    )

    # Parse the returned strings to validate their format
    parsed_start_utc = parser.parse(start_utc)
    parsed_end_utc = parser.parse(end_utc)

    # Check if the parsed objects are instances of datetime
    assert isinstance(parsed_start_utc, datetime)
    assert isinstance(parsed_end_utc, datetime)

    # Assert the values are as expected
    # assert start_utc == expected_start
    # assert end_utc == expected_end


@pytest.mark.parametrize(
    "date_str, time_str",
    [
        ("invalid-date", "12:00"),  # Invalid date
        ("2022-01-01", "invalid-time"),  # Invalid time
        # Add more test cases with invalid inputs
    ],
)
def test_prepare_utc_datetime_strings_invalid(date_str, time_str):
    start_utc, end_utc = GoogleMeetService._prepare_utc_datetime_strings(
        date_str, time_str
    )
    assert start_utc is None
    assert end_utc is None


# Test for successful event insertion
@patch("src.milap.main.uuid.uuid4", return_value="unique-id")
@patch(
    "src.milap.main.GoogleMeetService._prepare_utc_datetime_strings",
    return_value=("2022-01-01T12:00:00.000Z", "2022-01-01T12:45:00.000Z"),
)
def test_insert_calendar_event_success(mock_prepare_utc, mock_uuid4):
    service_mock = Mock()
    insert_mock = service_mock.events().insert()
    insert_mock.execute.return_value = {"id": "event-id"}  # Mocked response

    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    result = gms._insert_calendar_event(
        service_mock, "2022-01-01", "12:00", "Meeting Summary", "Meeting Description"
    )

    # Assertions
    assert result == {"id": "event-id"}
    # insert_mock.assert_called_once()
    mock_prepare_utc.assert_called_once()
    mock_uuid4.assert_called_once()


# Test for invalid date and time
@patch(
    "src.milap.main.GoogleMeetService._prepare_utc_datetime_strings",
    return_value=(None, None),
)
def test_insert_calendar_event_invalid_datetime(mock_prepare_utc):
    service_mock = Mock()

    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    result = gms._insert_calendar_event(
        service_mock,
        "invalid-date",
        "invalid-time",
        "Meeting Summary",
        "Meeting Description",
    )

    # Assertions
    assert result is None
    mock_prepare_utc.assert_called_once()
    service_mock.events().insert.assert_not_called()


# Test for failure due to HttpError
@patch("src.milap.main.uuid.uuid4", return_value="unique-id")
@patch(
    "src.milap.main.GoogleMeetService._prepare_utc_datetime_strings",
    return_value=("2022-01-01T12:00:00.000Z", "2022-01-01T12:45:00.000Z"),
)
def test_insert_calendar_event_http_error(mock_prepare_utc, mock_uuid4):
    service_mock = Mock()
    insert_mock = service_mock.events().insert()
    insert_mock.execute.side_effect = HttpError(Mock(status=404), b"Not found")

    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    result = gms._insert_calendar_event(
        service_mock, "2022-01-01", "12:00", "Meeting Summary", "Meeting Description"
    )

    # Assertions
    assert result is None
    # insert_mock.assert_called_once()
    mock_prepare_utc.assert_called_once()
    mock_uuid4.assert_called_once()


# Test when the slot is booked
@patch("src.milap.main.GoogleMeetService._get_service")
@patch(
    "src.milap.main.GoogleMeetService._prepare_utc_datetime_strings",
    return_value=("2022-01-01T12:00:00.000Z", "2022-01-01T12:45:00.000Z"),
)
def test_is_slot_booked_true(mock_prepare_utc, mock_get_service):
    mock_service = Mock()
    mock_get_service.return_value = mock_service
    mock_service.events().list().execute.return_value = {
        "items": [{"organizer": {"email": "organizer@example.com"}}]
    }

    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    result = gms.is_slot_booked("2022-01-01", "12:00", "organizer@example.com")

    assert result is True


# Test when the slot is not booked
@patch("src.milap.main.GoogleMeetService._get_service")
@patch(
    "src.milap.main.GoogleMeetService._prepare_utc_datetime_strings",
    return_value=("2022-01-01T12:00:00.000Z", "2022-01-01T12:45:00.000Z"),
)
def test_is_slot_booked_false(mock_prepare_utc, mock_get_service):
    mock_service = Mock()
    mock_get_service.return_value = mock_service
    mock_service.events().list().execute.return_value = {
        "items": [{"organizer": {"email": "other@example.com"}}]
    }

    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    result = gms.is_slot_booked("2022-01-01", "12:00", "organizer@example.com")

    assert result is False


# Test for failure due to HttpError
@patch("src.milap.main.GoogleMeetService._get_service")
@patch(
    "src.milap.main.GoogleMeetService._prepare_utc_datetime_strings",
    return_value=("2022-01-01T12:00:00.000Z", "2022-01-01T12:45:00.000Z"),
)
def test_is_slot_booked_error(mock_prepare_utc, mock_get_service):
    mock_service = Mock()
    mock_get_service.return_value = mock_service
    mock_service.events().list().execute.side_effect = HttpError(
        Mock(status=404), b"Not found"
    )

    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    result = gms.is_slot_booked("2022-01-01", "12:00", "organizer@example.com")

    assert result is False


# Test for successful event creation
@patch("src.milap.main.GoogleMeetService._get_service")
@patch(
    "src.milap.main.GoogleMeetService._insert_calendar_event",
    return_value={"id": "event-id"},
)
def test_create_meeting_event_success(mock_insert_calendar_event, mock_get_service):
    mock_service = Mock()
    mock_get_service.return_value = mock_service

    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    result = gms.create_meeting_event(
        "2022-01-01", "12:00", "Meeting Summary", "Meeting Description"
    )

    # Assertions
    assert result == {"id": "event-id"}
    mock_insert_calendar_event.assert_called_once_with(
        mock_service, "2022-01-01", "12:00", "Meeting Summary", "Meeting Description"
    )


# Test when service is unavailable
@patch("src.milap.main.GoogleMeetService._get_service", return_value=None)
def test_create_meeting_event_no_service(mock_get_service):
    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    result = gms.create_meeting_event(
        "2022-01-01", "12:00", "Meeting Summary", "Meeting Description"
    )

    # Assertions
    assert result is None


# Test for successful event update
@patch("src.milap.main.GoogleMeetService._get_service")
def test_update_meeting_event_success(mock_get_service):
    mock_service = Mock()
    mock_get_service.return_value = mock_service

    # Mocking the Google Calendar API methods
    mock_service.events().get().execute.return_value = {}
    mock_service.events().update().execute.return_value = {"updated": True}

    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    result = gms.update_meeting_event("event-id", {"summary": "Updated Meeting"})

    # Assertions
    assert result == {"updated": True}
    # mock_service.events().get.assert_called_once()
    # mock_service.events().update.assert_called_once()


# Test when service is unavailable
@patch("src.milap.main.GoogleMeetService._get_service", return_value=None)
def test_update_meeting_event_no_service(mock_get_service):
    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    result = gms.update_meeting_event("event-id", {"summary": "Updated Meeting"})

    # Assertions
    assert result is None


# Test for failure due to HttpError
@patch("src.milap.main.GoogleMeetService._get_service")
def test_update_meeting_event_http_error(mock_get_service):
    mock_service = Mock()
    mock_get_service.return_value = mock_service

    # Mocking the Google Calendar API methods
    mock_service.events().get().execute.side_effect = HttpError(
        Mock(status=404), b"Not found"
    )

    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    result = gms.update_meeting_event("event-id", {"summary": "Updated Meeting"})

    # Assertions
    assert result is None
    # mock_service.events().get.assert_called_once()


# Test for successful event deletion
@patch("src.milap.main.GoogleMeetService._get_service")
def test_delete_meeting_event_success(mock_get_service):
    mock_service = Mock()
    mock_get_service.return_value = mock_service

    # Mocking the Google Calendar API delete method
    mock_service.events().delete().execute.return_value = None

    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    result = gms.delete_meeting_event("event-id")

    # Assertions
    assert result is True
    # mock_service.events().delete.assert_called_once_with(
    #     calendarId="primary", eventId="event-id"
    # )


# Test when service is unavailable
@patch("src.milap.main.GoogleMeetService._get_service", return_value=None)
def test_delete_meeting_event_no_service(mock_get_service):
    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    result = gms.delete_meeting_event("event-id")

    # Assertions
    assert result is False


# Test for failure due to HttpError
@patch("src.milap.main.GoogleMeetService._get_service")
def test_delete_meeting_event_http_error(mock_get_service):
    mock_service = Mock()
    mock_get_service.return_value = mock_service

    # Mocking the Google Calendar API delete method to raise HttpError
    mock_service.events().delete().execute.side_effect = HttpError(
        Mock(status=404), b"Not found"
    )

    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    result = gms.delete_meeting_event("event-id")

    # Assertions
    assert result is False
    # mock_service.events().delete.assert_called_once_with(
    #     calendarId="primary", eventId="event-id"
    # )


# Test for successful fetching of events
@patch("src.milap.main.GoogleMeetService._get_service")
def test_fetch_meeting_by_criteria_success(mock_get_service):
    mock_service = Mock()
    mock_get_service.return_value = mock_service

    # Mocking the Google Calendar API list method
    mock_service.events().list().execute.return_value = {"items": [{"id": "event-id"}]}

    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    result = gms.fetch_meeting_by_criteria(
        "2022-01-01T00:00:00Z", "2022-01-02T00:00:00Z", "meeting"
    )

    # Assertions
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == {"id": "event-id"}
    # mock_service.events().list.assert_called_once()


# Test when service is unavailable
@patch("src.milap.main.GoogleMeetService._get_service", return_value=None)
def test_fetch_meeting_by_criteria_no_service(mock_get_service):
    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    result = gms.fetch_meeting_by_criteria(
        "2022-01-01T00:00:00Z", "2022-01-02T00:00:00Z", "meeting"
    )

    # Assertions
    assert result is None


# Test for failure due to HttpError
@patch("src.milap.main.GoogleMeetService._get_service")
def test_fetch_meeting_by_criteria_http_error(mock_get_service):
    mock_service = Mock()
    mock_get_service.return_value = mock_service

    # Mocking the Google Calendar API list method to raise HttpError
    mock_service.events().list().execute.side_effect = HttpError(
        Mock(status=404), b"Not found"
    )

    gms = GoogleMeetService("client_id", "client_secret", "refresh_token")
    result = gms.fetch_meeting_by_criteria(
        "2022-01-01T00:00:00Z", "2022-01-02T00:00:00Z", "meeting"
    )

    # Assertions
    assert result is None
    # mock_service.events().list.assert_called_once()
