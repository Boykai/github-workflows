# Backend Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
# Use --pre flag for agent-framework preview packages
RUN pip install --no-cache-dir --pre -e .

# Ensure the Copilot CLI binary is executable (bundled in github-copilot-sdk wheel)
RUN find /usr/local/lib/python3.12 -name "copilot" -type f -executable 2>/dev/null || true

# Copy application code
COPY src/ ./src/

# Create data directory for SQLite database (volume mount target)
RUN mkdir -p /app/data

# Create non-root user and set ownership
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health')" || exit 1

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
