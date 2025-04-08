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
        import logging
        logging.info(f"🔍 Retrieving documents for query: {query[:50]}...")
        
        # Comprobar si la consulta es sobre información de contacto
        contact_keywords = ["contact", "email", "phone", "address", "location", "reach"]
        is_contact_query = any(keyword in query.lower() for keyword in contact_keywords)
        logging.info(f"Is contact query: {is_contact_query}")
        
        # Usar un modelo de embeddings más robusto
        try:
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            logging.info("✅ Embeddings model loaded successfully")
        except Exception as e:
            logging.error(f"❌ Error loading embeddings model: {e}")
            return "I'm having trouble accessing my knowledge base right now. Here's what I know about QuistBuilder: We're a digital marketing agency specializing in SEO, web design, and online advertising. You can contact us at info@quistbuilder.com or (800) 650-2380."
        
        # Verificar que la base vectorial existe
        import os
        if not os.path.exists(CHROMA_DB_DIR):
            logging.error(f"⚠️ Vector database not found at {CHROMA_DB_DIR}")
            return "QuistBuilder is a digital marketing agency specializing in SEO, web design, and online advertising. You can contact us at info@quistbuilder.com or (800) 650-2380."
        
        # Cargar la base vectorial
        try:
            vectordb = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
            logging.info("✅ Vector database loaded successfully")
        except Exception as e:
            logging.error(f"❌ Error loading vector database: {e}")
            return "QuistBuilder is a digital marketing agency specializing in SEO, web design, and online advertising. You can contact us at info@quistbuilder.com or (800) 650-2380."
        
        # Si es una consulta de contacto, proporcionar información de contacto directamente
        if is_contact_query:
            contact_info = """## Contact Info

**Main Contact:**

📧 Email: info@quistbuilder.com
📞 Phone: (800) 650-2380
🌐 Website: www.quistbuilder.com

**Office Location:**

QuistBuilder
7901 Emerald Dr, Suite 15
Emerald Isle, NC 28594

**Office Hours:**

Monday – Friday: 9 AM – 6 PM EST
Closed Saturday & Sunday"""
            logging.info("✅ Returning hardcoded contact information")
            return contact_info
            
        # Búsqueda normal para otras consultas
        try:
            results = vectordb.similarity_search_with_score(query, k=k)
            
            if not results:
                # Si no hay resultados, intentar con el retriever estándar
                retriever = vectordb.as_retriever(search_kwargs={"k": k})
                docs = retriever.invoke(query)
                
                if not docs:
                    return "I don't have specific information about that in my knowledge base. QuistBuilder is a digital marketing agency specializing in SEO, web design, and online advertising. You can contact us at info@quistbuilder.com or (800) 650-2380."
                
                content = "\n\n".join(doc.page_content for doc in docs)
            else:
                # Procesar los resultados de similarity_search_with_score
                docs = [doc for doc, score in results]
                content = "\n\n".join(doc.page_content for doc in docs)
            
            return content
        except Exception as e:
            logging.error(f"❌ Error during document retrieval: {e}")
            return "I'm having trouble accessing my knowledge base right now. QuistBuilder is a digital marketing agency specializing in SEO, web design, and online advertising. You can contact us at info@quistbuilder.com or (800) 650-2380."
        

    except Exception as e:
        print(f"❌ Error retrieving documents: {e}")
        return "I'm having trouble accessing my knowledge base right now. Let me help you with what I know about QuistBuilder. We're a digital marketing agency specializing in SEO, web design, and online advertising."

if __name__ == "__main__":
    query = input("Enter your query: ")
    print("\nResults:")
    print(retrieve_documents(query))