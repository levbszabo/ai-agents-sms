from zoneinfo import ZoneInfo
import pytz
from datetime import datetime
from typing import *
from langchain.tools import BaseTool
import asyncio

from langchain_core.tools import BaseTool

import os
import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment variables
GOOGLE_CALENDAR_CLIENT_EMAIL = os.getenv("GOOGLE_CALENDAR_CLIENT_EMAIL")
GOOGLE_CALENDAR_PRIVATE_KEY = os.getenv("GOOGLE_CALENDAR_PRIVATE_KEY").replace(
    "\\n", "\n"
)
GOOGLE_CALENDAR_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_CALENDAR_ID")
DELEGATED_USER_EMAIL = os.getenv("DELEGATED_USER_EMAIL")  # Add this to your .env file
GOOGLE_CALENDAR_PROJECT_ID = os.getenv("GOOGLE_CALENDAR_PROJECT_ID")
GOOGLE_CALENDAR_PRIVATE_KEY_ID = os.getenv("GOOGLE_CALENDAR_PRIVATE_KEY_ID")
GOOGLE_CALENDAR_CLIENT_ID = os.getenv("GOOGLE_CALENDAR_CLIENT_ID")


# Define the scopes and credentials
SCOPES = ["https://www.googleapis.com/auth/calendar"]
credentials = Credentials.from_service_account_info(
    {
        "type": "service_account",
        "project_id": GOOGLE_CALENDAR_PROJECT_ID,
        "private_key_id": GOOGLE_CALENDAR_PRIVATE_KEY_ID,
        "private_key": GOOGLE_CALENDAR_PRIVATE_KEY,
        "client_email": GOOGLE_CALENDAR_CLIENT_EMAIL,
        "client_id": GOOGLE_CALENDAR_CLIENT_ID,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/"
        + GOOGLE_CALENDAR_CLIENT_EMAIL,
    },
    scopes=SCOPES,
)

# Delegate user email
credentials = credentials.with_subject(DELEGATED_USER_EMAIL)

# Build the service
service = build("calendar", "v3", credentials=credentials)


def create_event(summary, start_time, end_time, description="", attendees_emails=[]):
    attendees = [{"email": email} for email in attendees_emails]
    event = {
        "summary": summary,
        "description": description,
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "UTC",
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "UTC",
        },
        "attendees": attendees,
        "conferenceData": {
            "createRequest": {
                "requestId": "some-random-string",  # This should be a unique string
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    event = (
        service.events()
        .insert(
            calendarId=GOOGLE_CALENDAR_CALENDAR_ID, body=event, conferenceDataVersion=1
        )
        .execute()
    )
    return {
        "htmlLink": event.get("htmlLink"),
        "hangoutLink": event.get("hangoutLink", ""),
    }


# Example usage
if __name__ == "__main__":
    # Calculate next Friday's date and time
    today = datetime.datetime.now(pytz.utc)
    next_friday = today + datetime.timedelta((4 - today.weekday()) % 7 + 1)
    start_time = next_friday.replace(hour=16, minute=0, second=0, microsecond=0)
    # Assume the meeting lasts 1 hour
    end_time = start_time + datetime.timedelta(hours=1)

    # Create a meeting with John Doe and add attendees
    result = create_event(
        summary="Meeting with John Doe",
        start_time=start_time,
        end_time=end_time,
        description="Adding to the agenda of it the result of 99 + 99",
        attendees_emails=["levente@journeymanai.io", "levbszabo@gmail.com"],
    )

EST = ZoneInfo("America/New_York")


class CalendarBookingTool(BaseTool):
    name = "calendar_booking"
    description = """Book a meeting on the calendar. Require details including summary, start time, end time, description, and attendee emails.
    Always book the call with levente@journeymanai.io and the user's given email.
    When using the calendar_booking tool, ensure you provide all required information in the correct format:
    - summary: A brief description of the meeting (string)
    - start_time: The start time in EST format (YYYY-MM-DD HH:MM AM/PM)
    - end_time: The end time in EST format (YYYY-MM-DD HH:MM AM/PM)
    - description: Additional details  (string, optional)
    - attendee_emails: Comma-separated list of attendee email addresses (string, optional)
    Use (EST).
    calendar_booking: {
        "summary": "Project Discussion",
        "start_time": "2023-07-01 02:00 PM",
        "end_time": "2023-07-01 03:00 PM",
        "description": "Discuss project milestones",
        "attendee_emails": "jane@example.com"
    }
    """

    def _run(self, **kwargs: Dict[str, Any]) -> str:
        try:
            summary = kwargs.get("summary")
            start_time = kwargs.get("start_time")
            end_time = kwargs.get("end_time")
            description = kwargs.get("description", "")
            attendee_emails = kwargs.get("attendee_emails", "")

            if not all([summary, start_time, end_time]):
                raise ValueError(
                    "Missing required parameters: summary, start_time, or end_time"
                )

            # Parse the input times as EST
            start = datetime.strptime(start_time, "%Y-%m-%d %I:%M %p").replace(
                tzinfo=EST
            )
            end = datetime.strptime(end_time, "%Y-%m-%d %I:%M %p").replace(tzinfo=EST)

            # Convert to UTC for storage
            start_utc = start.astimezone(pytz.UTC)
            end_utc = end.astimezone(pytz.UTC)

            if start >= end:
                raise ValueError("End time must be after start time")

            # Always include levente@journeymanai.io and parse other attendees
            attendees_list = ["levente@journeymanai.io"]
            if attendee_emails:
                attendees_list.extend(
                    [email.strip() for email in attendee_emails.split(",")]
                )

            # Remove duplicates while preserving order
            attendees_list = list(dict.fromkeys(attendees_list))

            result = create_event(
                summary, start_utc, end_utc, description, attendees_list
            )

            # Convert the result times back to EST for display
            start_est = start_utc.astimezone(EST)
            end_est = end_utc.astimezone(EST)

            # Log successful creation

            return f"Meeting booked in EST. Start: {start_est.strftime('%Y-%m-%d %I:%M %p')} EST, End: {end_est.strftime('%Y-%m-%d %I:%M %p')} EST. Attendees: {', '.join(attendees_list)}. Link: {result['htmlLink']}, Google Meet: {result['hangoutLink']}"

        except ValueError as ve:
            return f"Error: {str(ve)}"
        except Exception as e:
            # Log any unexpected errors
            return f"An unexpected error occurred: {str(e)}"

    async def _arun(self, **kwargs: Dict[str, Any]) -> str:
        return await asyncio.to_thread(self._run, **kwargs)
