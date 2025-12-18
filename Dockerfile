FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY harness/ harness/

# Use environment variables for config
ENV OLLAMA_HOST=ollama.harness.svc.cluster.local:11434
ENV QDRANT_HOST=qdrant.harness.svc.cluster.local
ENV QDRANT_PORT=6333

CMD ["python", "-m", "harness"]