# PROVES Library - Docker Image
# Multi-stage build for efficient extraction pipeline

FROM python:3.14-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 proves && chown -R proves:proves /app
USER proves

# Set up Python environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/proves/.local/bin:$PATH"

# Copy requirements first (for caching)
COPY --chown=proves:proves requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=proves:proves . .

# Clone PROVES_NOTION repo (required for Notion integration)
RUN git clone https://github.com/Lizo-RoadTown/PROVES_NOTION.git PROVES_NOTION

# Default command - run extraction pipeline
CMD ["python", "production/Version 3/process_extractions_v3.py"]

# Build webhook server image
FROM base as webhook

# Expose webhook server port
EXPOSE 8000

# Run webhook server
CMD ["python", "notion/scripts/notion_webhook_server.py"]
