# Use the official Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-back.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements-back.txt

# Copy application code
COPY . .

# Expose the port Cloud Run uses
EXPOSE 8080

# Create a script to check and rebuild the vector database if needed
RUN echo '#!/bin/bash' > /app/check_db.sh && \
    echo 'if [ ! -d "chroma_db" ] || [ -z "$(ls -A chroma_db 2>/dev/null)" ]; then' >> /app/check_db.sh && \
    echo '  echo "📚 Vector database not found. Rebuilding..."' >> /app/check_db.sh && \
    echo '  python md_to_chroma.py' >> /app/check_db.sh && \
    echo '  echo "✅ Vector database rebuilt successfully."' >> /app/check_db.sh && \
    echo 'fi' >> /app/check_db.sh && \
    chmod +x /app/check_db.sh

# Run the check script and then start uvicorn
CMD /app/check_db.sh && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
