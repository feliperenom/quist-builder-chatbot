import os
import pypdf
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

import sys
import os

# Determinar si estamos en desarrollo o producción
if os.path.exists("model/data"):
    # Estamos en desarrollo (ruta relativa al directorio raíz)
    DATA_DIR = "model/data"
    CHROMA_DB_DIR = "model/chroma_db"
else:
    # Estamos en producción (ruta relativa al directorio actual)
    DATA_DIR = "data"
    CHROMA_DB_DIR = "chroma_db"

def extract_text_from_markdown(directory):
    """Extracts text from all Markdown files in a folder."""
    documents = []

    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            filepath = os.path.join(directory, filename)
            print(f"📄 Reading file: {filepath}")

            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()

            documents.append(Document(page_content=text, metadata={"source": filename}))
    
    return documents

def split_text_into_chunks(documents, chunk_size=250, chunk_overlap=50):
    """Splits documents into chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    return text_splitter.split_documents(documents)

def store_in_chroma(chunks):
    """Stores the chunks in a Chroma vector database."""
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_DB_DIR)
    vectordb.persist()
    return vectordb

if __name__ == "__main__":
    docs = extract_text_from_markdown(DATA_DIR)
    chunks = split_text_into_chunks(docs)
    vectordb = store_in_chroma(chunks)
    print(f"\nVector database created in '{CHROMA_DB_DIR}' with {len(chunks)} chunks.")