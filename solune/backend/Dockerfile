# syntax=docker/dockerfile:1
# Backend Dockerfile — multi-stage build

# ── Builder stage: install system deps + Python packages ──
FROM python:3.14-slim AS builder

WORKDIR /app

# Install build-time system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies with BuildKit cache
# Use --pre flag for agent-framework preview packages
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --pre -e .

# Ensure the Copilot CLI binary is executable (bundled in github-copilot-sdk wheel)
RUN find /usr/local/lib/python3.14 -name "copilot" -type f -executable 2>/dev/null || true

# ── Runtime stage: slim image without build tools ──
FROM python:3.14-slim AS runtime

WORKDIR /app

# Copy installed Python packages and binaries from builder
COPY --from=builder /usr/local/lib/python3.14 /usr/local/lib/python3.14
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/

# Copy template files for new repository scaffolding
COPY templates/ /app/templates/
ENV TEMPLATE_SOURCE_DIR=/app/templates

# Create data directory for SQLite database (volume mount target)
RUN mkdir -p /var/lib/solune/data

# Create non-root user and set ownership
RUN useradd --create-home appuser && chown -R appuser:appuser /app /var/lib/solune/data
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
