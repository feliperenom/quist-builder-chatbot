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
    try:
        # Comprobar si la consulta es sobre información de contacto
        contact_keywords = ["contact", "email", "phone", "address", "location", "reach"]
        is_contact_query = any(keyword in query.lower() for keyword in contact_keywords)
        
        # Usar un modelo de embeddings más robusto
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Verificar que la base vectorial existe
        import os
        if not os.path.exists(CHROMA_DB_DIR):
            print(f"⚠️ Vector database not found at {CHROMA_DB_DIR}")
            return "No vector database found. Please contact support."
        
        # Cargar la base vectorial
        vectordb = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
        
        # Si es una consulta de contacto, buscar específicamente información de contacto
        if is_contact_query:
            # Usar una consulta específica para encontrar información de contacto
            contact_results = vectordb.similarity_search_with_score("QuistBuilder contact information email phone address", k=2)
            if contact_results:
                contact_docs = [doc for doc, score in contact_results]
                return "\n\n".join(doc.page_content for doc in contact_docs)
        
        # Búsqueda normal para otras consultas
        results = vectordb.similarity_search_with_score(query, k=k)
        
        if not results:
            # Si no hay resultados, intentar con el retriever estándar
            retriever = vectordb.as_retriever(search_kwargs={"k": k})
            docs = retriever.invoke(query)
            
            if not docs:
                return "I don't have specific information about that in my knowledge base. Could you please ask about our services, contact information, or other details about QuistBuilder?"
            
            content = "\n\n".join(doc.page_content for doc in docs)
        else:
            # Procesar los resultados de similarity_search_with_score
            docs = [doc for doc, score in results]
            content = "\n\n".join(doc.page_content for doc in docs)
        
        return content
    except Exception as e:
        print(f"❌ Error retrieving documents: {e}")
        return "I'm having trouble accessing my knowledge base right now. Let me help you with what I know about QuistBuilder. We're a digital marketing agency specializing in SEO, web design, and online advertising."

if __name__ == "__main__":
    query = input("Enter your query: ")
    print("\nResults:")
    print(retrieve_documents(query))