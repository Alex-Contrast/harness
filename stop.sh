#!/bin/bash

echo "Stopping Harness dependencies..."

# Stop Qdrant
if docker ps --format '{{.Names}}' | grep -q '^qdrant$'; then
    echo "Stopping Qdrant..."
    docker stop qdrant
else
    echo "Qdrant not running"
fi

# Stop Ollama
if pgrep -x "ollama" > /dev/null; then
    echo "Stopping Ollama..."
    pkill -x ollama
else
    echo "Ollama not running"
fi

echo "Done."
