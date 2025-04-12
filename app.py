import streamlit as st
import requests
import time
import re
import uuid
from sentence_transformers import SentenceTransformer, util

st.set_page_config(page_title="QuistBuilder Chatbot", layout="centered")
st.title("💬 QuistBuilder AI Assistant")
st.markdown("Welcome! Ask anything about our services, contact info, or what we do 💡")
st.markdown("---")

# Inicializar estado
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "user_phone" not in st.session_state:
    st.session_state.user_phone = ""

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "email_sent_up_to_index" not in st.session_state:
    st.session_state.email_sent_up_to_index = -1

# Cargar modelo solo una vez
if "embed_model" not in st.session_state:
    st.session_state.embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# Frases semilla para detectar confirmación
seed_phrases = [
    "please send it to the email I gave",
    "you can use the email I already mentioned",
    "contact me at the previous email",
    "send it to the same email",
    "reach out to me using my email",
    "at the above email address",
    "use my email",
    "send the information to my email",
    "you can send it now",
    "schedule it via email",
]

# Mostrar historial previo
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada del usuario
if prompt := st.chat_input("Type your message..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 🔎 Buscar email/teléfono explícitos
    email_match = re.search(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", prompt)
    phone_match = re.search(r"\+?\d[\d\s\-]{7,}", prompt)

    new_email = email_match.group().strip() if email_match else None
    new_phone = phone_match.group().strip() if phone_match else None

    already_sent = st.session_state.email_sent_up_to_index >= len(st.session_state.messages)

    # 🔁 Detectar confirmación por similitud semántica
    prompt_embedding = st.session_state.embed_model.encode(prompt, convert_to_tensor=True)
    seed_embeddings = st.session_state.embed_model.encode(seed_phrases, convert_to_tensor=True)
    similarity_scores = util.cos_sim(prompt_embedding, seed_embeddings)
    max_sim = similarity_scores.max().item()
    confirmation_detected = max_sim > 0.75

    # 📩 Lógica para decidir envío
    if (new_email or new_phone) and not already_sent:
        if new_email:
            st.session_state.user_email = new_email
        if new_phone:
            st.session_state.user_phone = new_phone
        should_send = True

    elif confirmation_detected and not already_sent and (
        st.session_state.user_email or st.session_state.user_phone
    ):
        should_send = True
    else:
        should_send = False

    # Enviar email si corresponde
    if should_send:
        transcript = ""
        for m in st.session_state.messages:
            role = "User" if m["role"] == "user" else "Assistant"
            transcript += f"{role}: {m['content']}\n\n"

        requests.post("http://localhost:8000/send-email", json={
            "name": "Unknown",
            "email": st.session_state.user_email,
            "phone": st.session_state.user_phone,
            "chat_history": transcript
        })

        st.session_state.email_sent_up_to_index = len(st.session_state.messages)

    # 🧠 Armar historial completo
    chat_history = ""
    for m in st.session_state.messages:
        role = "User" if m["role"] == "user" else "Assistant"
        chat_history += f"{role}: {m['content']}\n\n"

    # 🔁 Llamar al backend con streaming
    with st.chat_message("assistant"):
        start_time = time.time()
        placeholder = st.empty()

        try:
            with st.spinner("Generating response..."):
                response = requests.post(
                    "http://localhost:8000/ask/stream",
                    json={
                        "query": prompt,
                        "chat_history": chat_history,
                        "user_email": st.session_state.user_email,
                        "user_phone": st.session_state.user_phone,
                        "session_id": st.session_state.session_id
                    },
                    stream=True,
                    timeout=60
                )

                full_response = ""
                for chunk in response.iter_content(chunk_size=None):
                    decoded = chunk.decode("utf-8")
                    full_response += decoded
                    placeholder.markdown(full_response)

                elapsed = time.time() - start_time
                st.caption(f"⏱️ Response time: {elapsed:.2f} seconds")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response
                })

        except requests.exceptions.RequestException as e:
            st.error(f"❌ Request failed: {e}")
