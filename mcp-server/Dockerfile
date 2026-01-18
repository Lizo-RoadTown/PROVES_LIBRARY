# PROVES Library MCP Server
# Multi-stage build for smaller image
#
# Build:   docker build -t proves-mcp .
# Run:     docker run -p 8000:8000 -e DATABASE_URL=... proves-mcp

# ============================================
# Stage 1: Build
# ============================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY source_registry.yaml ./

# Install dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy source files (needed for registry path resolution)
COPY --from=builder /app/src ./src
COPY --from=builder /app/source_registry.yaml ./

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HOST=0.0.0.0

# Health check - simple TCP check since MCP endpoints vary
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.settimeout(5); s.connect(('localhost',8000)); s.close()" || exit 1

# Expose port
EXPOSE ${PORT}

# Run the MCP server with streamable-http transport
CMD ["python", "-m", "proves_mcp.server", "--transport", "streamable-http", "--port", "8000"]
