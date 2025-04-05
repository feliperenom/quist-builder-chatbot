import os
import re
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from typing import Optional, TypedDict
from langgraph.graph import END, StateGraph
from langchain_google_vertexai import ChatVertexAI
from langchain.prompts.chat import ChatPromptTemplate

# Load environment variables
load_dotenv()
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ----------- STATE ----------- #
class ContactState(TypedDict, total=False):
    input: str
    session_id: str
    is_first_message: Optional[bool]
    email: Optional[str]
    name: Optional[str]
    email_sent: Optional[bool]
    error: Optional[str]
    response: Optional[str]

# ----------- NODE 0: Greeting (only for first message) ----------- #
def greeting_node(state: ContactState) -> ContactState:
    if state.get("is_first_message"):
        greeting = (
            "Hey there! I’m the QuistBuilder assistant—excited to help you out!\n"
            "To get started, may I have your name, email, and a bit about the service you’re looking for?"
        )
        print(">>> [AGENT] Sending initial greeting.")
        state["greeting"] = greeting
    else:
        print(">>> [AGENT] No greeting sent. Not the first message.")
    return state

# ----------- NODE 1: Extract contact info ----------- #
def extract_info(state: ContactState) -> ContactState:
    text = state["input"]
    print(">>> [AGENT] Received text:", text)

    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    
    # CORREGIDO: eliminar doble barra \\
    name_match = re.search(r"\bmy name is ([A-Z][a-z]+)", text, re.IGNORECASE)
    if not name_match:
        name_match = re.search(r"\bI am ([A-Z][a-z]+)", text, re.IGNORECASE)
    if not name_match:
        name_match = re.search(r"\bI'm ([A-Z][a-z]+)", text, re.IGNORECASE)

    if name_match:
        print(">>> [AGENT] Name detected:", name_match.group(1))
    if email_match:
        print(">>> [AGENT] Email detected:", email_match.group(0))

    return {
        **state,
        "email": email_match.group(0) if email_match else None,
        "name": name_match.group(1) if name_match else None
    }

# ----------- NODE 2: Decision ----------- #
def should_send_email(state: ContactState) -> str:
    if state.get("email") or state.get("name"):
        return "send_email"
    return "skip_email"

# ----------- NODE 3: Send email ----------- #
def send_email(state: ContactState) -> ContactState:
    name = state.get("name") or "Not provided"
    email = state.get("email") or "Not provided"
    message = state.get("input", "")

    body = f"""\n🚨 New contact detected:\n\nName: {name}\nEmail: {email}\n\nMessage:\n{message}\n"""

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

# ----------- NODE 4: Generate response ----------- #
def generate_response(state: ContactState) -> ContactState:
    question = state["input"]
    llm = ChatVertexAI(model_name="gemini-2.0-flash-001", temperature=0.0, max_tokens=2000)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        ("human", "{question}")
    ])

    messages = prompt.format_messages(question=question)
    result = llm(messages)

    full_response = result.content
    if "greeting" in state:
        full_response = f"{state['greeting']}\n\n{full_response}"
        del state["greeting"]

    state["response"] = full_response
    return state

# ----------- BUILD THE AGENT ----------- #
def create_contact_agent():
    builder = StateGraph(ContactState)

    builder.add_node("greeting_node", greeting_node)
    builder.add_node("extract_info", extract_info)
    builder.add_node("send_email", send_email)
    builder.add_node("generate_response", generate_response)

    builder.set_entry_point("greeting_node")
    builder.add_edge("greeting_node", "extract_info")

    builder.add_conditional_edges(
        "extract_info",
        should_send_email,
        {
            "send_email": "send_email",
            "skip_email": "generate_response"
        }
    )

    builder.add_edge("send_email", "generate_response")
    builder.add_edge("generate_response", END)

    return builder.compile()