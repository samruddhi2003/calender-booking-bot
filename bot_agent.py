from langchain_community.chat_models import ChatFireworks
from langchain_core.callbacks.manager import CallbackManager
from langchain.agents import initialize_agent, Tool
from langchain.tools import tool
from langchain.agents import AgentExecutor
from dotenv import load_dotenv
import os
import requests
import re
from datetime import datetime

# Load environment variables
load_dotenv()

# Init Fireworks LLM
llm = ChatFireworks(
    model="accounts/fireworks/models/llama4-maverick-instruct-basic",
    api_key=os.getenv("FIREWORKS_API_KEY"),
    temperature=0.5,
    streaming=False,
    callback_manager=CallbackManager([]),
)

# 📅 Tool: Book an event
@tool
def book_event(user_input: str) -> str:
    """
    Book a calendar event using input like:
    'Book Team Meeting from 2025-07-04T10:00:00 to 2025-07-04T11:00:00'
    """
    try:
        match = re.search(r"book (.+?) from ([\d\-T:]+) to ([\d\-T:]+)", user_input, re.IGNORECASE)
        if not match:
            return "❌ Invalid format. Use: 'Book [title] from [start_time] to [end_time]'"

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

            return f"✅ Event '{summary}' booked on {user_friendly_start} to {user_friendly_end}. [View event]({event_link})\n\n✅ Booking complete. No further action needed."
        else:
            return f"❌ Error {response.status_code}: {response.text}"

    except Exception as e:
        return f"❌ Exception: {e}"

# 🕒 Tool: Get available slots
@tool
def get_available_slots_tool(_: str) -> str:
    """
    Returns available 1-hour time slots for today.
    """
    try:
        response = requests.get("https://calender-booking-bot.onrender.com/slots")
        if response.status_code == 200:
            slots = response.json().get("available_slots", [])
            if not slots:
                return "❌ No available slots found today."
            return "✅ Available slots today:\n" + "\n".join(f"- {slot}" for slot in slots)
        else:
            return f"❌ Failed to fetch slots. Status: {response.status_code}"
    except Exception as e:
        return f"❌ Exception while getting slots: {e}"

# Combine tools
tools = [book_event, get_available_slots_tool]

# Init agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent_type="zero-shot-react-description",
    verbose=True,
    handle_parsing_errors=True
)

executor = AgentExecutor(agent=agent, tools=tools, max_iterations=3)
