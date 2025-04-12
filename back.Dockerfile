# Use Python 3.9 as the base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements-back.txt .
RUN pip install --no-cache-dir -r requirements-back.txt

# Copy the application code
COPY . .

# Set environment variables
ENV PORT=8080

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD exec uvicorn app:app --host 0.0.0.0 --port $PORT