from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag import get_context
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
from typing import Optional
from pathlib import Path
import smtplib
from email.message import EmailMessage
import re

load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Question(BaseModel):
    query: str
    chat_history: str = ""
    user_email: str = ""
    user_phone: str = ""
    session_id: str

class ContactInfo(BaseModel):
    name: str
    email: str
    phone: str
    chat_history: str

def send_meeting_email(name: str, email: str, phone: str, chat_history: str = ""):
    msg = EmailMessage()
    msg["Subject"] = "📅 New Contact via Chatbot"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    body = (
        f"A user shared contact details via the chatbot:\n\n"
        f"Name: {name}\nEmail: {email}\nPhone: {phone}\n\n"
    )

    if chat_history:
        body += "Chat Transcript:\n\n" + chat_history

    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Email sent for contact: {email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

system_prompt_path = Path("system_prompt.md")
with system_prompt_path.open("r", encoding="utf-8") as f:
    system_prompt = f.read()

@app.post("/ask/stream")
async def stream_answer(question: Question):
    try:
        context = get_context(question.query)

        user_content = f"Context:\n{context}\n\nConversation history:\n{question.chat_history}\n\n"
        if question.user_email:
            user_content += f"The user has already provided their email address: {question.user_email}.\n"
        user_content += f"\nNow answer this question:\n{question.query}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        async def token_stream():
            stream = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                temperature=0,
                messages=messages,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        # En este endpoint no se envía ningún email
        headers = {"X-Email-Sent": "false"}
        return StreamingResponse(token_stream(), media_type="text/plain", headers=headers)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-email")
def send_final_email(data: ContactInfo):
    send_meeting_email(data.name, data.email, data.phone, data.chat_history)
    return {"status": "ok"}