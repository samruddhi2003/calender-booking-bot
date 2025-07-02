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
    Book a calendar event using casual language like:
    'Schedule lunch with John tomorrow from 1pm to 2pm'
    """
    try:
        # 🔥 Call Fireworks to parse the input
        prompt = f"""
        You are a helpful assistant that extracts calendar booking information from user input.
        Input: "{user_input}"
        Output JSON:
        {{
            "summary": "Meeting with HR",
            "start_time": "2025-10-19T03:00:00",
            "end_time": "2025-10-19T04:00:00"
        }}
        """

        headers = {
            "Authorization": f"Bearer {os.getenv('FIREWORKS_API_KEY')}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "accounts/fireworks/models/llama4-maverick-instruct-basic",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }

        response = requests.post("https://api.fireworks.ai/inference/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

        import json
        event_data = json.loads(content)

        # 📅 Call backend to book the event
        res = requests.post("https://calender-booking-bot.onrender.com/book", json=event_data)

        if res.status_code == 200:
            start = datetime.fromisoformat(event_data["start_time"]).strftime("%B %d, %Y at %I:%M %p")
            end = datetime.fromisoformat(event_data["end_time"]).strftime("%I:%M %p")
            link = res.json().get("event_link")
            return f"✅ '{event_data['summary']}' booked from {start} to {end}. [View event]({link})"
        else:
            return f"❌ Error {res.status_code}: {res.text}"

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
