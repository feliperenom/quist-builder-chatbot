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
    logging.info("✅ Vertex AI initialized successfully")
except Exception as e:
    logging.error(f"❌ Error initializing Vertex AI: {e}")
    # No lanzar la excepción, permitir que la aplicación continúe
    logging.warning("⚠️ Continuing without Vertex AI initialization")

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
async def chat(request: ChatRequest):
    try:
        logging.info(f"📩 Received chat request: {request.prompt[:50]}...")
        
        session_id = request.session_id
        is_first_message = session_id not in seen_sessions
        seen_sessions.add(session_id)
        
        # Step 1: Process with contact agent
        try:
            agent = create_contact_agent()
            
            agent_output = agent.invoke({
                "input": request.prompt,
                "session_id": session_id
            })
            logging.info("✅ Contact agent processed successfully")
        except Exception as e:
            logging.error(f"❌ Error in contact agent: {e}")
            agent_output = {"name": None, "email": None, "email_sent": False, "error": str(e)}

        # Step 2: Retrieve relevant context
        try:
            # Aumentar el número de documentos a recuperar para mejorar la cobertura
            context = retrieve_documents(request.prompt, k=15)
            if not context.strip():
                # Proporcionar información básica sobre QuistBuilder si no se encuentra contexto específico
                context = "QuistBuilder is a results-driven internet marketing agency based in Emerald Isle, NC. We've been helping businesses grow for over 10 years with powerful websites, SEO, paid ads, and AI integrations. Our team builds optimized websites, drives targeted traffic, and helps convert that traffic into real leads and customers."
        except Exception as e:
            logging.error(f"❌ Error retrieving context: {e}")
            # Proporcionar información básica en caso de error
            context = "QuistBuilder is a digital marketing agency specializing in website design, SEO, paid advertising, and AI integration. We help businesses grow their online presence and generate more leads."

        # Step 3: Build full prompt
        full_prompt = f"""{SYSTEM_PROMPT}

        Context:
        {context}

        User question:
        {request.prompt}
        """

        # Step 4: Get response from Gemini-Pro
        try:
            logging.info("🤖 Invoking Gemini-Pro model")
            response = chat_model.invoke(full_prompt)
            bot_reply = response.content if response else "⚠️ Could not generate a response."
            logging.info("✅ Gemini-Pro response generated successfully")
        except Exception as e:
            logging.error(f"❌ Error invoking Gemini-Pro: {e}", exc_info=True)
            # Proporcionar una respuesta alternativa en caso de error
            bot_reply = "I'm currently experiencing some technical difficulties. Please try again later or contact QuistBuilder directly at info@quistbuilder.com or (800) 650-2380."

        # Si es el primer mensaje Y no hay una pregunta específica, mostrar el saludo
        # Pero si hay una pregunta específica (como información de contacto), responder a ella
        if is_first_message and not any(keyword in request.prompt.lower() for keyword in ["contact", "email", "phone", "address", "location", "reach"]):
            greeting = (
                "Hey there! I'm the QuistBuilder assistant—excited to help you out!\n"
                "To get started, may I have your name, email, and a bit about the service you're looking for?"
            )
            bot_reply = greeting  # Use only the greeting, without adding the model's response

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