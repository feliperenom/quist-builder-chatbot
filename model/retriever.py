from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

import os

# Determinar si estamos en desarrollo o producción
if os.path.exists("model/chroma_db"):
    # Estamos en desarrollo (ruta relativa al directorio raíz)
    CHROMA_DB_DIR = "model/chroma_db"
else:
    # Estamos en producción (ruta relativa al directorio actual)
    CHROMA_DB_DIR = "chroma_db"

def retrieve_documents(query, k=3):
    """Retrieves relevant documents from ChromaDB"""
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)

    retriever = vectordb.as_retriever(search_kwargs={"k": k})
    docs = retriever.invoke(query)
    
    if not docs:
        return "No relevant information found in the documents."
    
    content = "\n\n".join(doc.page_content for doc in docs)
    return content

if __name__ == "__main__":
    query = input("Enter your query: ")
    print("\nResults:")
    print(retrieve_documents(query))