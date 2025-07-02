from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import json
import requests

# 🔃 Load environment variables
load_dotenv()

app = FastAPI()

# 🔐 Load credentials securely from env variable
SERVICE_ACCOUNT_INFO = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
if not SERVICE_ACCOUNT_INFO:
    raise RuntimeError("Missing GOOGLE_SERVICE_ACCOUNT_JSON environment variable")

CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")

credentials = service_account.Credentials.from_service_account_info(
    json.loads(SERVICE_ACCOUNT_INFO),
    scopes=['https://www.googleapis.com/auth/calendar']
)

# 🔧 Build Google Calendar service
service = build('calendar', 'v3', credentials=credentials)

# 📦 Request models
class EventRequest(BaseModel):
    summary: str
    start_time: str  # e.g., '2025-07-01T14:00:00'
    end_time: str    # e.g., '2025-07-01T15:00:00'

class NaturalLanguageRequest(BaseModel):
    message: str

# 📅 Route to book calendar event
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


# 💬 Route to parse user message and book via Fireworks LLM
@app.post("/nlp-book")
def nlp_book(request: NaturalLanguageRequest):
    try:
        print(f"🤖 Fireworks interpreting: {request.message}")

        # Call Fireworks LLM API
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
            "messages": [
                {"role": "user", "content": prompt}
            ],
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
