# PROVES Extraction API - Dockerfile
#
# IMPORTANT: Build from the project root, not the extraction-api folder!
#
# Build:
#   docker build -t proves-extraction-api -f extraction-api/Dockerfile .
#
# Run:
#   docker run -p 8080:8080 --env-file .env proves-extraction-api

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY extraction-api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API code
COPY extraction-api/app.py ./app.py

# Copy the production folder (extraction pipeline)
COPY production ./production

# Copy canon folder (for FRAMES methodology references)
COPY canon ./canon

# Expose the port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the API
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
