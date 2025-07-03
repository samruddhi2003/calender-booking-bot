from langchain_community.chat_models import ChatFireworks
from langchain_core.callbacks.manager import CallbackManager
from langchain.agents import initialize_agent, Tool
from langchain.tools import tool
from dotenv import load_dotenv
import os
import requests
import re
from datetime import datetime

load_dotenv()

llm = ChatFireworks(
    model="accounts/fireworks/models/llama4-maverick-instruct-basic",
    api_key=os.getenv("FIREWORKS_API_KEY"),
    temperature=0.5,
    streaming=False,
    callback_manager=CallbackManager([]),
)

# 📅 Book event tool
@tool
def book_event(user_input: str) -> str:
    """
    Book a calendar event. Input like:
    'Book Standup from 2025-07-04T09:00 to 2025-07-04T09:30'
    """
    try:
        match = re.search(r"book (.+?) from ([\d\-T:]+) to ([\d\-T:]+)", user_input, re.IGNORECASE)
        if not match:
            return ("❌ I couldn't understand the event details. Please say something like:\n"
                    "`Book Team Sync from 2025-07-07T15:00 to 2025-07-07T16:00`")

        summary, start_time, end_time = match.groups()

        response = requests.post("https://calender-booking-bot.onrender.com/book", json={
            "summary": summary,
            "start_time": start_time,
            "end_time": end_time
        })

        if response.status_code == 200:
            user_friendly_start = datetime.fromisoformat(start_time).strftime("%B %d, %Y at %I:%M %p")
            user_friendly_end = datetime.fromisoformat(end_time).strftime("%I:%M %p")
            event_link = response.json().get("event_link")
            return f"✅ '{summary}' booked from {user_friendly_start} to {user_friendly_end}. [View]({event_link})"
        else:
            return f"❌ Failed to book event. Error {response.status_code}: {response.text}"

    except Exception as e:
        return f"❌ Exception while booking: {e}"

# 🕒 Get available slots tool
@tool
def get_available_slots(user_input: str) -> str:
    """
    Ask about availability: 'What time am I free today?' or 'Show slots'
    """
    if not re.search(r"\b(free|available|slots?)\b", user_input.lower()):
        return "❓ Please ask about your availability."

    try:
        response = requests.get("https://calender-booking-bot.onrender.com/available")
       if response.status_code == 200:
         data = response.json()
         slots = data.get("available_slots", [])
       if not slots:
        return "✅ You're completely free today! 🕊️"
        return "📅 Your schedule today:\n" + "\n".join(f"• {slot}" for slot in slots)


    except Exception as e:
        return f"❌ Failed to retrieve availability: {e}"

# Tools list
tools = [book_event, get_available_slots]

# LangChain Agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent_type="zero-shot-react-description",
    verbose=True,
    handle_parsing_errors=True
)
