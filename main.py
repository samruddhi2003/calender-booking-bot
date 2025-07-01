from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

app = FastAPI()

# Load credentials
SERVICE_ACCOUNT_FILE = 'service_account.json'
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/calendar']
)

# Build Google Calendar service
service = build('calendar', 'v3', credentials=credentials)

# 📦 Define the request model
class EventRequest(BaseModel):
    summary: str
    start_time: str  # Format: '2025-07-01T14:00:00'
    end_time: str    # Format: '2025-07-01T15:00:00'

# 🚀 Route to book calendar event
@app.post("/book")
def book_event(event: EventRequest):
    try:
        print(f"📅 Booking Event: {event.summary} from {event.start_time} to {event.end_time}")

        event_body = {
            'summary': event.summary,
            'start': {
                'dateTime': event.start_time,
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': event.end_time,
                'timeZone': 'Asia/Kolkata',
            },
        }

        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event_body).execute()

        return {
            'status': 'success',
            'event_link': created_event.get('htmlLink'),
            'event_id': created_event.get('id'),
        }

    except Exception as e:
        print(f"❌ Exception while booking: {e}")
        raise HTTPException(status_code=500, detail=str(e))
