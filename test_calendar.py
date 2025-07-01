from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# Path to your downloaded service account key
SERVICE_ACCOUNT_FILE = 'service_account.json'

# Replace with your calendar's email (your email or service account email if using new calendar)
CALENDAR_ID = 'calendar-bot-service@micro-progress-464615-g9.iam.gserviceaccount.com'  # <- Change this

# Authenticate with the service account
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/calendar']
)

# Build the Google Calendar API client
service = build('calendar', 'v3', credentials=creds)

# Set start and end times for event
now = datetime.utcnow()
event = {
    'summary': 'Test Event from Python',
    'start': {
        'dateTime': (now + timedelta(hours=1)).isoformat() + 'Z',
        'timeZone': 'UTC',
    },
    'end': {
        'dateTime': (now + timedelta(hours=2)).isoformat() + 'Z',
        'timeZone': 'UTC',
    },
}

# Insert the event
created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()

print(f"✅ Event created: {created_event.get('htmlLink')}")

from google.oauth2 import service_account
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = 'service_account.json'
CALENDAR_ID = 'calendar-bot-service@micro-progress-464615-g9.iam.gserviceaccount.com'
USER_EMAIL = 'vidyakulkarni9636@gmail.com'  # your email

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/calendar']
)

service = build('calendar', 'v3', credentials=credentials)

rule = {
    'scope': {
        'type': 'user',
        'value': USER_EMAIL,
    },
    'role': 'owner'
}

created_rule = service.acl().insert(calendarId=CALENDAR_ID, body=rule).execute()
print(f"✅ Calendar shared with {USER_EMAIL}")

