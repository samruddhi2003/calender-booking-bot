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

# Google credentials
SERVICE_ACCOUNT_INFO = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
if not SERVICE_ACCOUNT_INFO:
    raise RuntimeError("Missing GOOGLE_SERVICE_ACCOUNT_JSON")

CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")

credentials = service_account.Credentials.from_service_account_info(
    json.loads(SERVICE_ACCOUNT_INFO),
    scopes=["https://www.googleapis.com/auth/calendar"]
)

# Google Calendar service
service = build("calendar", "v3", credentials=credentials)

# Request model
class EventRequest(BaseModel):
    summary: str
    start_time: str  # ISO format
    end_time: str    # ISO format

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
        now = datetime.datetime.now().isoformat()
        end_of_day = (datetime.datetime.now().replace(hour=23, minute=59, second=59)).isoformat()

        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=now,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        busy_slots = [(e["start"]["dateTime"], e["end"]["dateTime"]) for e in events if "dateTime" in e["start"]]

        all_slots = []
        start_hour = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
        for i in range(10):  # Next 10 hours
            start_slot = start_hour + datetime.timedelta(hours=i)
            end_slot = start_slot + datetime.timedelta(hours=1)
            slot_str = (start_slot.isoformat(), end_slot.isoformat())

            if not any(
                bs[0] < slot_str[1] and bs[1] > slot_str[0]
                for bs in busy_slots
            ):
                all_slots.append(f"{start_slot.strftime('%I:%M %p')} to {end_slot.strftime('%I:%M %p')}")

        return {"available_slots": all_slots}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Calendar Bot is running 🚀"}
