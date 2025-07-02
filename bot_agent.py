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

# Initialize Fireworks LLM
llm = ChatFireworks(
    model="accounts/fireworks/models/llama4-maverick-instruct-basic",
    api_key=os.getenv("FIREWORKS_API_KEY"),
    temperature=0.5,
    streaming=False,
    callback_manager=CallbackManager([]),
)

# Tool: Book event in calendar
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

# Tool list
tools = [book_event]

# Initialize agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent_type="zero-shot-react-description",
    verbose=True,
    handle_parsing_errors=True
)

# Wrap agent to limit unnecessary retries
executor = AgentExecutor(agent=agent, tools=tools, max_iterations=3)

# CLI loop
if __name__ == "__main__":
    while True:
        user_input = input("🗣️ You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        result = executor.run(user_input)
        print("🤖 Bot:", result)
