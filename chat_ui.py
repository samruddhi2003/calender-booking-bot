import streamlit as st
from bot_agent import agent

st.set_page_config(page_title="🗓️ Calendar Booking Bot", layout="centered")
st.title("🤖 Calendar Booking Assistant")
st.markdown("""
Ask me to book meetings like:  
`Book Team Sync from 2025-07-07T15:00:00 to 2025-07-07T16:00:00`  
Or ask: `What time am I free today?`, `Show available slots`, `Am I free this afternoon?`
""")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"], unsafe_allow_html=True)

# New message input
user_input = st.chat_input("What would you like to do?")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            try:
                response = agent.invoke(user_input)
                if isinstance(response, dict):
                    response = response.get("output", str(response))
            except Exception as e:
                response = f"❌ Error: {e}"

            st.markdown(response, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": response})
