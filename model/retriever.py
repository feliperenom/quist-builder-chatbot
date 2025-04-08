from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import os

# Determinar las rutas correctas basadas en la ubicación actual
current_dir = os.path.dirname(os.path.abspath(__file__))

# Si estamos en la carpeta model, usar rutas relativas a la carpeta actual
if os.path.basename(current_dir) == 'model':
    CHROMA_DB_DIR = os.path.join(current_dir, "chroma_db")
else:
    # Si estamos en otra ubicación, usar rutas absolutas
    CHROMA_DB_DIR = os.path.join(current_dir, "chroma_db")

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