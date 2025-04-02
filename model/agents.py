import os
import re
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from typing import Optional, TypedDict

from langgraph.graph import END, StateGraph
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate

# Cargar variables de entorno
load_dotenv()
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ----------- ESTADO ----------- #
class ContactState(TypedDict, total=False):
    input: str
    email: Optional[str]
    name: Optional[str]
    email_sent: Optional[bool]
    error: Optional[str]
    response: Optional[str]

# ----------- NODO 1: Extraer info ----------- #
def extract_info(state: ContactState) -> ContactState:
    text = state["input"]
    print(">>> [AGENTE] Texto recibido:", text)

    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    name_match = re.search(r"\bmy name is ([A-Z][a-z]+)", text, re.IGNORECASE)
    
    if name_match:
        print(">>> [AGENTE] Nombre detectado:", name_match.group(1))
    if email_match:
        print(">>> [AGENTE] Email detectado:", email_match.group(0))

    return {
        **state,
        "email": email_match.group(0) if email_match else None,
        "name": name_match.group(1) if name_match else None
    }

# ----------- NODO 2: Decisión ----------- #
def should_send_email(state: ContactState) -> str:
    if state.get("email") or state.get("name"):
        return "send_email"
    return "skip_email"

# ----------- NODO 3: Enviar email ----------- #
def send_email(state: ContactState) -> ContactState:
    name = state.get("name") or "Not provided"
    email = state.get("email") or "Not provided"
    message = state.get("input", "")

    body = f"""🚨 New contact detected:

Name: {name}
Email: {email}

Message:
{message}
"""

    msg = MIMEText(body)
    msg["Subject"] = "🚨 New chatbot lead"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        state["email_sent"] = True
    except Exception as e:
        state["email_sent"] = False
        state["error"] = str(e)

    return state

# ----------- NODO 4: Generar respuesta LLM ----------- #
def generate_response(state: ContactState) -> ContactState:
    question = state["input"]
    llm = ChatOpenAI(model_name="gpt-3.5-turbo")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        ("human", "{question}")
    ])

    messages = prompt.format_messages(question=question)
    result = llm(messages)

    state["response"] = result.content
    return state

# ----------- AGENTE: CONSTRUCCIÓN ----------- #
def create_contact_agent():
    builder = StateGraph(ContactState)

    builder.add_node("extract_info", extract_info)
    builder.add_node("send_email", send_email)
    builder.add_node("generate_response", generate_response)

    builder.set_entry_point("extract_info")

    # Evaluar si debe enviar email
    builder.add_conditional_edges(
        "extract_info",
        should_send_email,
        {
            "send_email": "send_email",
            "skip_email": "generate_response"
        }
    )

    # Si envió el email, sigue a respuesta
    builder.add_edge("send_email", "generate_response")
    builder.add_edge("generate_response", END)

    return builder.compile()
