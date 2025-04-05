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

# Start FastAPI using Uvicorn on port 8080
CMD ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8080"]
