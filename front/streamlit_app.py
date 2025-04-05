import streamlit as st
import requests
import uuid

# ---------------- CONFIG ----------------
API_URL = "http://localhost:8000/chat"

st.set_page_config(page_title="QuistBuilder Chatbot", layout="wide")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.title("QuistBuilder Chatbot")
    st.markdown("---")
    st.markdown("📄 Model: Gemini + ChromaDB")

# ---------- GLOBAL STATE ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# ---------- TITLE ----------
st.title("💬 WhatsApp-style Chat")

# ---------- DISPLAY MESSAGE HISTORY ----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------- USER INPUT ----------
if prompt := st.chat_input("Type your message..."):
    # Show the user's message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Build the payload with current input only
    payload = {
        "prompt": prompt,
        "session_id": st.session_state.session_id
    }

    # Call the backend API
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        answer = response.json().get("response", "⚠️ Unable to generate a response.")
    except Exception as e:
        answer = f"⚠️ Error connecting to the API: {e}"

    # Show the assistant's response
    st.chat_message("assistant").markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
