import streamlit as st
from bot_agent import agent  # This should be your AgentExecutor or initialized agent

# Page config
st.set_page_config(page_title="🗓️ Calendar Booking Bot", layout="centered")

# Title and instruction
st.title("🤖 Calendar Booking Assistant")
st.markdown("""
Ask me to book meetings like:  
`Book Team Sync from 2025-07-07T15:00:00 to 2025-07-07T16:00:00`
""")

# Store messages in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"], unsafe_allow_html=True)

# Handle user input
user_input = st.chat_input("What would you like to book?")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            response = agent.run(user_input)

            # Directly render the response (already contains Markdown link)
            st.markdown(response, unsafe_allow_html=True)

            st.session_state.messages.append({"role": "assistant", "content": response})
