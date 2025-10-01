# Single-stage Dockerfile for CIPetteLens
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FLASK_PORT=5001 \
    FLASK_DEBUG=False

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./

# Copy application code
COPY cipettelens/ ./cipettelens/
COPY templates/ ./templates/
COPY static/ ./static/

# Install dependencies
RUN uv sync --extra dev

# Create necessary directories
RUN mkdir -p logs db

# Create non-root user
RUN groupadd -r cipettelens && useradd -r -g cipettelens cipettelens
RUN chown -R cipettelens:cipettelens /app

# Switch to non-root user
USER cipettelens

# Expose port
EXPOSE ${FLASK_PORT:-5001}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${FLASK_PORT:-5001}/ || exit 1

# Default command
CMD ["uv", "run", "web"]