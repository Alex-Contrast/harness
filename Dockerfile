FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl xz-utils openjdk-21-jre-headless && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js (direct download for ARM64)
RUN curl -fsSL https://nodejs.org/dist/v20.11.0/node-v20.11.0-linux-arm64.tar.xz -o /tmp/node.tar.xz && \
    tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 && \
    rm /tmp/node.tar.xz && \
    node --version && npm --version && \
    echo "update-notifier=false" > /root/.npmrc

# Download Contrast MCP server JAR
RUN curl -L -o /opt/mcp-contrast.jar \
    https://github.com/Contrast-Security-OSS/mcp-contrast/releases/latest/download/mcp-contrast.jar

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY harness/ harness/

# Default env vars (overridden by K8s ConfigMap)
ENV OLLAMA_HOST=http://ollama.harness.svc.cluster.local:11434
ENV QDRANT_HOST=qdrant.harness.svc.cluster.local
ENV QDRANT_PORT=6333
ENV NPM_CONFIG_UPDATE_NOTIFIER=false

CMD ["python", "-m", "harness"]