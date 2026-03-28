# syntax=docker/dockerfile:1
# Backend Dockerfile — multi-stage build with uv

# ── Builder stage: install dependencies with uv ──
FROM python:3.14-slim AS builder

# Copy uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:0.10.9 /uv /uvx /bin/

# Compile bytecode for faster cold starts; copy mode required in Docker
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies first (cached layer) — lockfile ensures reproducibility
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-editable

# Copy application source and sync the project itself
COPY src/ ./src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

# ── Runtime stage: slim image without build tools ──
FROM python:3.14-slim AS runtime

WORKDIR /app

# Copy the virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

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
