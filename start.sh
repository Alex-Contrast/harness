#!/bin/bash

echo "Starting Harness dependencies..."

# Start Ollama (if not already running)
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama..."
    ollama serve &
    sleep 2
else
    echo "Ollama already running"
fi

# Start Qdrant (if not already running)
if ! docker ps --format '{{.Names}}' | grep -q '^qdrant$'; then
    if docker ps -a --format '{{.Names}}' | grep -q '^qdrant$'; then
        echo "Starting existing Qdrant container..."
        docker start qdrant
    else
        echo "Creating and starting Qdrant container..."
        docker run -d --name qdrant \
            -p 6333:6333 -p 6334:6334 \
            -v ~/.qdrant/storage:/qdrant/storage \
            qdrant/qdrant
    fi
else
    echo "Qdrant already running"
fi

# Wait for services to be ready
echo "Waiting for services..."
sleep 5

# Verify services
echo ""
echo "Checking services..."

printf "Ollama: "
curl -s http://localhost:11434/api/tags > /dev/null && echo "OK" || echo "FAILED"

printf "Qdrant: "
for i in 1 2 3 4 5; do
    if curl -s http://localhost:6333/ | grep -q qdrant; then
        echo "OK"
        break
    fi
    if [ $i -eq 5 ]; then
        echo "FAILED"
    else
        sleep 1
    fi
done

echo ""
echo "Ready! Run 'swift run HarnessAgent' to start the agent."
