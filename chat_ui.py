import streamlit as st
from bot_agent import agent

# Config
st.set_page_config(page_title="🗓️ Calendar Booking Bot", layout="centered")
st.title("🤖 Calendar Booking Assistant")

st.markdown("""
Ask me to:
- `Book Team Sync from 2025-07-07T15:00:00 to 2025-07-07T16:00:00`
- `What time am I free today?`
""")

# Store chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render past chat
for msg in st.session_state.messages:
    avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"], unsafe_allow_html=True)

# Chat input
user_input = st.chat_input("What would you like to book or check?")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            response = agent.run(user_input)
            st.markdown(response, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": response})
