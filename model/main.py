import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from retriever import retrieve_documents
from agents import create_contact_agent
from google.cloud import aiplatform
from pydantic import BaseModel
from langchain_google_vertexai import ChatVertexAI

# Load env variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get environment variables
project_id = os.getenv("PROJECT_ID")
service_account_key = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Verify that environment variables have been set 
if not service_account_key or not project_id:
    raise ValueError("Environment variables are not correctly set.")

# ───────────────────────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────

# credentials_path = "/tmp/service-account.json"

# try:
#      with open(credentials_path, "w") as f:
#          f.write(service_account_key)
#      os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
# except Exception as e:
#      raise RuntimeError(f"Error al escribir el archivo de credenciales: {e}")

# ───────────────────────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────

# Initialize VertexAI
try:
    aiplatform.init(project=project_id, location="us-central1")
except Exception as e:
    logging.error(f"Error initializing Vertex AI: {e}")
    raise

seen_sessions = set()

# Logging setup
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load system prompt from external file
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

# Initialize contact agent
agent = create_contact_agent()

# Load Gemini-Pro model
chat_model = ChatVertexAI(model_name="gemini-2.0-flash-001", temperature=0.0, max_output_tokens=2000)

class ChatRequest(BaseModel):
    prompt: str
    session_id: str

@app.post("/chat")
def chat(request: ChatRequest):
    try:
        session_id = request.session_id or "default_session"
        is_first_message = session_id not in seen_sessions

        if is_first_message:
            seen_sessions.add(session_id)

        # Step 1: Run contact agent
        agent_output = agent.invoke({
            "input": request.prompt,
            "session_id": session_id
        })

        # Step 2: Retrieve relevant context
        try:
            context = retrieve_documents(request.prompt, k=10)
            if not context.strip():
                context = "No relevant information found in the knowledge base."
        except Exception as e:
            logging.error(f"❌ Error retrieving context: {e}")
            context = "Error retrieving context."

        # Step 3: Build full prompt
        full_prompt = f"""{SYSTEM_PROMPT}

        Context:
        {context}

        User question:
        {request.prompt}
        """

        # Step 4: Get response from Gemini-Pro
        try:
            response = chat_model.invoke(full_prompt)
            bot_reply = response.content if response else "⚠️ Could not generate a response."
        except Exception as e:
            logging.error(f"❌ Error invoking Gemini-Pro: {e}", exc_info=True)
            bot_reply = f"⚠️ Error: {str(e)}"

        # Add welcome message if it's the first message in the session
        if is_first_message:
            greeting = (
                "Hey there! I’m the QuistBuilder assistant—excited to help you out!\n"
                "To get started, may I have your name, email, and a bit about the service you’re looking for?"
            )
            bot_reply = f"{greeting}\n\n{bot_reply}"

        return {
            "response": bot_reply,
            "detected_name": agent_output.get("name"),
            "detected_email": agent_output.get("email"),
            "email_sent": agent_output.get("email_sent", False),
            "error": agent_output.get("error")
        }

    except Exception as e:
        logging.error(f"❌ General error in /chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"message": "Chat API with Gemini-Pro and RAG is running successfully."}