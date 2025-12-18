#!/bin/bash

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Configurable values with defaults
MINIKUBE_CPUS=${MINIKUBE_CPUS:-4}
MINIKUBE_MEMORY=${MINIKUBE_MEMORY:-12g}
OLLAMA_MODE=${OLLAMA_MODE:-host}

echo "Starting Harness K8s infrastructure..."
echo "  Ollama mode: $OLLAMA_MODE"

# Start minikube if not running
if ! minikube status | grep -q "Running"; then
    echo "Starting minikube (cpus=$MINIKUBE_CPUS, memory=$MINIKUBE_MEMORY)..."
    minikube start --cpus=$MINIKUBE_CPUS --memory=$MINIKUBE_MEMORY
else
    echo "Minikube already running"
fi

# Apply K8s manifests
echo "Applying K8s manifests..."
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/qdrant/

if [ "$OLLAMA_MODE" = "k8s" ]; then
    # K8s mode: deploy Ollama in cluster, mount models
    echo "Mounting Ollama models from host..."
    pkill -f "minikube mount" 2>/dev/null || true
    minikube mount ~/.ollama:/ollama-models &>/dev/null &
    sleep 2

    kubectl apply -f k8s/ollama/
    kubectl apply -f k8s/harness/configmap-k8s-ollama.yml
else
    # Host mode: use native Ollama, bound to all interfaces for K8s access
    if ! pgrep -x "ollama" > /dev/null; then
        echo "Starting local Ollama (bound to 0.0.0.0)..."
        OLLAMA_HOST=0.0.0.0:11434 ollama serve &>/dev/null &
        sleep 3
    else
        echo "Local Ollama already running"
        echo "  Note: Ensure it was started with OLLAMA_HOST=0.0.0.0:11434"
    fi

    kubectl apply -f k8s/harness/configmap-host-ollama.yml
fi

kubectl apply -f k8s/harness/deployment.yml
kubectl apply -f k8s/harness/pdb.yml

# Wait for pods to be created and ready
echo "Waiting for pods to be ready..."
sleep 5
if [ "$OLLAMA_MODE" = "k8s" ]; then
    kubectl -n harness wait --for=condition=ready pod -l app=ollama --timeout=120s 2>/dev/null || \
        echo "  Ollama still starting..."
fi
kubectl -n harness wait --for=condition=ready pod -l app=qdrant --timeout=120s 2>/dev/null || \
    echo "  Qdrant still starting..."
kubectl -n harness wait --for=condition=ready pod -l app=harness --timeout=120s 2>/dev/null || \
    echo "  Harness still starting..."

# Kill any existing port-forwards
pkill -f "kubectl.*port-forward.*harness" 2>/dev/null || true

# Start port forwarding in background
echo "Starting port forwards..."
if [ "$OLLAMA_MODE" = "k8s" ]; then
    kubectl -n harness port-forward svc/ollama 11434:11434 &>/dev/null &
fi
kubectl -n harness port-forward svc/qdrant 6333:6333 &>/dev/null &

# Wait for port forwards to establish
sleep 2

# Verify services
echo ""
echo "Checking services..."

printf "Ollama: "
curl -s http://localhost:11434/api/tags > /dev/null && echo "OK" || echo "FAILED"

printf "Qdrant: "
curl -s http://localhost:6333/collections > /dev/null && echo "OK" || echo "FAILED"

echo ""
echo "Ready! Run 'kubectl -n harness attach -it deployment/harness' to use the agent."
