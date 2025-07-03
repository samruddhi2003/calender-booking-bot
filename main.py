from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import json
import datetime

# Load environment variables
load_dotenv()

app = FastAPI()

# Load credentials
SERVICE_ACCOUNT_INFO = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
if not SERVICE_ACCOUNT_INFO:
    raise RuntimeError("Missing GOOGLE_SERVICE_ACCOUNT_JSON")

CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")

credentials = service_account.Credentials.from_service_account_info(
    json.loads(SERVICE_ACCOUNT_INFO),
    scopes=["https://www.googleapis.com/auth/calendar"]
)

# Calendar service
service = build("calendar", "v3", credentials=credentials)

# Request models
class EventRequest(BaseModel):
    summary: str
    start_time: str
    end_time: str

@app.post("/book")
def book_event(event: EventRequest):
    try:
        event_body = {
            "summary": event.summary,
            "start": {"dateTime": event.start_time, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": event.end_time, "timeZone": "Asia/Kolkata"},
        }
        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event_body).execute()
        return {
            "status": "success",
            "event_link": created_event.get("htmlLink"),
            "event_id": created_event.get("id"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/available")
def get_available_slots():
    try:
        print("📅 Checking available slots...")

        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        available_slots = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            available_slots.append(f"{start} to {end}")

        return {
            "available_slots": available_slots,
            "count": len(available_slots),
            "message": "📅 These are your upcoming events today." if available_slots else "✅ You're free today! 🎉"
        }

    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "trace": traceback.format_exc()
        }


@app.get("/")
def root():
    return {"message": "Calendar Bot is running 🚀"}
