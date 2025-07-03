# 📄 chat_ui.py (Streamlit frontend)
import streamlit as st
from bot_agent import agent

# UI Config
st.set_page_config(page_title="🗓️ Calendar Booking Bot", layout="centered")
st.title("🤖 Calendar Booking Assistant")
st.markdown("""
Ask me to book meetings like:  
- `Book Team Sync from 2025-07-07T15:00:00 to 2025-07-07T16:00:00`  
- `What time am I free today?`  
- `Show available slots`  
- `Am I free this afternoon?`
""")

# Chat session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages
for msg in st.session_state.messages:
    avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"], unsafe_allow_html=True)

# Get user input
user_input = st.chat_input("What would you like to book or check?")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            try:
                response = agent.invoke(user_input)  # Updated from .run to .invoke
                if isinstance(response, dict):
                    response = response.get("output", str(response))
            except Exception as e:
                response = f"❌ Sorry, something went wrong: {e}"
            st.markdown(response, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": response})
