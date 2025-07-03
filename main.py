from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import json
import requests
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

app = FastAPI()

# Load service account from environment
SERVICE_ACCOUNT_INFO = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
if not SERVICE_ACCOUNT_INFO:
    raise RuntimeError("Missing GOOGLE_SERVICE_ACCOUNT_JSON environment variable")

CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")

credentials = service_account.Credentials.from_service_account_info(
    json.loads(SERVICE_ACCOUNT_INFO),
    scopes=['https://www.googleapis.com/auth/calendar']
)

# Google Calendar API
service = build('calendar', 'v3', credentials=credentials)

# Models
class EventRequest(BaseModel):
    summary: str
    start_time: str
    end_time: str

class NaturalLanguageRequest(BaseModel):
    message: str

# Route to book calendar event
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


# Route to extract event data via Fireworks LLM
@app.post("/nlp-book")
def nlp_book(request: NaturalLanguageRequest):
    try:
        print(f"🤖 Fireworks interpreting: {request.message}")

        headers = {
            "Authorization": f"Bearer {FIREWORKS_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = f"""
        You are an assistant that extracts calendar booking information from user input.
        Input: "{request.message}"
        Output (in JSON):
        {{
            "summary": "...",
            "start_time": "2025-07-01T14:00:00",
            "end_time": "2025-07-01T15:00:00"
        }}
        """

        payload = {
            "model": "accounts/fireworks/models/llama-v2-7b-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }

        response = requests.post(
            "https://api.fireworks.ai/inference/v1/chat/completions",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        completion = response.json()["choices"][0]["message"]["content"]
        print("🧠 Fireworks response:", completion)

        event_data = json.loads(completion)
        return book_event(EventRequest(**event_data))

    except Exception as e:
        print(f"❌ Fireworks NLP error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# New: Get today's available 1-hour slots
@app.get("/slots")
def get_available_slots():
    try:
        now = datetime.utcnow()
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)

        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=now.isoformat() + 'Z',
            timeMax=end_of_day.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        # Check free 1-hour blocks
        available_slots = []
        current = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

        while current + timedelta(hours=1) <= end_of_day:
            slot_start = current
            slot_end = current + timedelta(hours=1)

            conflict = any(
                (datetime.fromisoformat(e['start']['dateTime'].replace("Z", "+00:00")) < slot_end and
                 datetime.fromisoformat(e['end']['dateTime'].replace("Z", "+00:00")) > slot_start)
                for e in events if 'dateTime' in e['start']
            )

            if not conflict:
                ist_start = slot_start + timedelta(hours=5, minutes=30)
                ist_end = slot_end + timedelta(hours=5, minutes=30)
                slot_str = f"{ist_start.strftime('%I:%M %p')} to {ist_end.strftime('%I:%M %p')}"
                available_slots.append(slot_str)

            current += timedelta(hours=1)

        return {"available_slots": available_slots}

    except Exception as e:
        print(f"❌ Error fetching slots: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Root health check
@app.get("/")
def root():
    return {"message": "Calendar Bot is running 🚀"}
