# FloatChat Python backend
# Runs the FastAPI server on port 8000.
#
# Build:  docker build -t floatchat-backend .
# Run:    docker run --env-file .env -p 8000:8000 floatchat-backend

FROM python:3.11-slim

WORKDIR /app

# System dependencies for psycopg2 and scientific packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libgeos-dev \
    proj-bin \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests first (layer-cache friendly)
COPY pyproject.toml ./
COPY agentic_workflow/requirements.txt ./agentic_workflow/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[server]"

# Copy application source
COPY agentic_workflow/ ./agentic_workflow/
COPY scripts/ ./scripts/

# Non-root user for security
RUN useradd -m -u 1001 floatchat
USER floatchat

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "agentic_workflow.api:app", "--host", "0.0.0.0", "--port", "8000"]
