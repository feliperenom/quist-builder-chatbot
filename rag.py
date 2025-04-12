import json
from sentence_transformers import SentenceTransformer
import chromadb

# Initialize model and Chroma client
model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection("quist_docs")

# Only embed documents if the collection is empty
if collection.count() == 0:
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    documents = []

    # Company overview
    documents.append(data["company_overview"])

    # Services
    # Combine all services into a single text block
    services_text = "Services Offered:\n\n"
    for k, v in data["services"].items():
        if v.strip():
            services_text += f"**{k.replace('_', ' ').title()}**\n{v.strip()}\n\n"

    documents.append(services_text)

    # Contact and others
    contact = data["contact_info"]
    documents.append(f"Main contact: {contact['main_contact']}")
    documents.append(f"Address: {contact['office_location']['address']}")
    documents.append(f"Office hours: {contact['office_hours']}")
    documents.append(f"Service area: {data['service_area']}")

    # Generate embeddings
    embeddings = model.encode(documents)

    # Store in vector database
    for i, doc in enumerate(documents):
        collection.add(
            ids=[str(i)],
            documents=[doc],
            embeddings=[embeddings[i]]
        )

def get_context(query: str) -> str:
    # Realiza búsqueda semántica
    results = collection.query(query_texts=[query], n_results=3)
    top_chunks = results["documents"][0]  # Lista de strings

    context = "\n\n".join(top_chunks)

    # ✅ Siempre asegurá que el overview esté incluido al inicio
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    company_overview = data.get("company_overview", "")
    if company_overview and company_overview not in context:
        context = f"Company Overview:\n{company_overview}\n\n{context}"

    return context


