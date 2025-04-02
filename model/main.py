from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
import os
import logging
from agents import create_contact_agent
from rag import extract_text_from_docx, chunk_text, build_vectorstore, get_retriever

# ---------------- Logging ---------------- #
logging.basicConfig(
    filename="debug.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------------- Configuración ---------------- #
DOC_PATH = "data/Response Guide - QuistBuilder.docx"
PERSIST_DIR = "chroma_db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Cargar variables de entorno
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Inicializar FastAPI
app = FastAPI()

# Variables globales
retriever = None
agent = None

# ---------------- Startup ---------------- #
@app.on_event("startup")
def startup_event():
    global retriever, agent

    logging.info(">>> [STARTUP] Inicializando pipeline con agente integrado...")

    # Procesar documento Word
    text = extract_text_from_docx(DOC_PATH)
    chunks = chunk_text(text)
    build_vectorstore(chunks)

    # Inicializar vectorstore
    retriever = get_retriever()

    # Crear agente una sola vez
    agent = create_contact_agent()

    logging.info("✅ [STARTUP] Sistema listo para responder.")

# ---------------- Endpoint ---------------- #
class QueryRequest(BaseModel):
    question: str

@app.post("/query")
def query(request: QueryRequest):
    global agent

    logging.info(">>> [QUERY] Endpoint recibido.")
    logging.info(">>> Pregunta: %s", request.question)

    # Ejecutar agente (extrae nombre/email, manda email si corresponde y responde con LLM)
    agent_result = agent.invoke({"input": request.question})

    logging.info(">> 🔍 Estado completo del agente: %s", agent_result)

    logging.info(">> Nombre detectado: %s", agent_result.get("name"))
    logging.info(">> Email detectado: %s", agent_result.get("email"))
    logging.info(">> Email enviado: %s", agent_result.get("email_sent"))
    if agent_result.get("error"):
        logging.error("❌ Error al enviar email: %s", agent_result["error"])
    logging.info(">> Respuesta del agente: %s", agent_result.get("response"))

    return {
        "response": agent_result.get("response"),
        "detected_name": agent_result.get("name"),
        "detected_email": agent_result.get("email"),
        "email_sent": agent_result.get("email_sent", False),
        "error": agent_result.get("error")
    }