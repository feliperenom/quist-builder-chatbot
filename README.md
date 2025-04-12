# QuistBuilder RAG Chat System

This is a Retrieval-Augmented Generation (RAG) system that allows you to chat with QuistBuilder's company data using natural language queries. The system uses LangChain, VectorDB (ChromaDB), and Hugging Face embeddings to provide accurate responses based on the provided JSON data.

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. (Optional) Create a `.env` file in the root directory with your Hugging Face API token:

```
HUGGINGFACE_API_TOKEN=your_huggingface_token_here
```

Note: If you don't provide a Hugging Face token, the system will fall back to a smaller model that doesn't require authentication, but the quality of responses may be lower.

3. Initialize the RAG system by processing the JSON data:

```bash
python initialize_rag.py
```

This will:
- Process the JSON data from `data/data.json`
- Create embeddings using the Hugging Face model
- Store the vector database in the `chroma_db` directory

## Usage

### Command Line Interface

You can interact with the RAG system using the command-line interface:

```bash
# Interactive mode
python cli.py

# Single query mode
python cli.py --query "What services does QuistBuilder offer?"
```

### API Server

You can also run the API server to interact with the RAG system via HTTP requests:

```bash
# Start the API server
python api.py
```

The server will run on `http://localhost:8000` with the following endpoints:

- `POST /chat`: Send a query to the RAG system
  - Request body: `{"query": "Your question here"}`
  - Response: `{"response": "Answer from the RAG system"}`

- `GET /health`: Health check endpoint

## Customization

You can customize the RAG system by modifying the following:

- Embedding model: Change the model in `initialize_rag.py` with the `--embedding_model` parameter
- Data source: Change the JSON file with the `--data_file` parameter in `initialize_rag.py`
- LLM model: Modify the model in `rag_chat.py`

## Example Queries

- "What services does QuistBuilder offer?"
- "Where is QuistBuilder located?"
- "What is QuistBuilder's contact information?"
- "What is QuistBuilder's service area?"
- "Tell me about QuistBuilder's AI integration services."
