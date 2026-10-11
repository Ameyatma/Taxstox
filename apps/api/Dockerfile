# TaxStox Backend — Production Docker image
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for PDF parsing + psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# DATABASE_URL is set via Render env vars (Neon PostgreSQL)
# No local data directory needed — PostgreSQL is remote.

# Cloud Run injects the PORT environment variable
ENV PORT=8080
EXPOSE $PORT

# Use shell form to evaluate the $PORT variable dynamically
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT}"]
