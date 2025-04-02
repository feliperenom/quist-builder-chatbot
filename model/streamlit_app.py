import streamlit as st
import requests

# ---------------- CONFIG ----------------
API_URL = "http://localhost:8000/query"

st.set_page_config(page_title="RAG Chatbot", layout="wide")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.title("💬 RAG Chatbot")
    st.markdown("Chat estilo WhatsApp con contexto")
    st.markdown("---")
    st.markdown("📄 Modelo: GPT-3.5 + ChromaDB")
    st.markdown("🧠 Usa un documento Word embebido")
    st.markdown("---")
    st.markdown("👨‍💻 Hecho por Felipe")

# ---------- CONTEXTO DE CONVERSACIÓN ----------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Soy tu asistente. ¿En qué puedo ayudarte hoy?"}
    ]

# ---------- TÍTULO ----------
st.title("💬 Chat estilo WhatsApp")

# ---------- MOSTRAR HISTORIAL ----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------- ENTRADA DEL USUARIO ----------
if prompt := st.chat_input("Escribí tu mensaje..."):
    # Mostrar mensaje del usuario
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Crear historial resumido (solo últimos turnos)
    history = st.session_state.messages[-6:]  # puedes ajustar esta cantidad

    # Crear una pregunta con contexto
    history_text = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in history if m['role'] != 'assistant'])

    # Llamar a tu API
    try:
        response = requests.post(API_URL, json={"question": f"{history_text}\nUser: {prompt}"})
        answer = response.json().get("response", "Lo siento, no pude procesar tu pregunta.")
    except Exception as e:
        answer = f"⚠️ Error al conectar con la API: {e}"

    # Mostrar respuesta del bot
    st.chat_message("assistant").markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
