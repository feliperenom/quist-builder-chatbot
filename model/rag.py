from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from docx import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

# Configuración
DOC_PATH = "data/Response Guide - QuistBuilder.docx"
PERSIST_DIR = "chroma_db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SYSTEM_PROMPT_PATH = "system_prompt.txt"

# Funciones auxiliares
def load_system_prompt(path=SYSTEM_PROMPT_PATH):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def chunk_text(text, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.create_documents([text])

def build_vectorstore(docs):
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    vectordb = Chroma.from_documents(docs, embedding=embeddings, persist_directory=PERSIST_DIR)
    vectordb.persist()

def get_retriever():
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    vectordb = Chroma(embedding_function=embeddings, persist_directory=PERSIST_DIR)
    return vectordb.as_retriever()
