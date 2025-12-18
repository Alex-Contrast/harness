#!/bin/bash

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Configurable values with defaults
MINIKUBE_CPUS=${MINIKUBE_CPUS:-4}
MINIKUBE_MEMORY=${MINIKUBE_MEMORY:-12g}
OLLAMA_MODE=${OLLAMA_MODE:-host}
NAMESPACE=${HELM_NAMESPACE:-harness-helm}

echo "Starting Harness K8s infrastructure (Helm)..."
echo "  Namespace: $NAMESPACE"
echo "  Ollama mode: $OLLAMA_MODE"

# Start minikube if not running
if ! minikube status | grep -q "Running"; then
    echo "Starting minikube (cpus=$MINIKUBE_CPUS, memory=$MINIKUBE_MEMORY)..."
    minikube start --cpus=$MINIKUBE_CPUS --memory=$MINIKUBE_MEMORY
else
    echo "Minikube already running"
fi

# Handle Ollama mode
if [ "$OLLAMA_MODE" = "k8s" ]; then
    echo "Mounting Ollama models from host..."
    pkill -f "minikube mount" 2>/dev/null || true
    minikube mount ~/.ollama:/ollama-models &>/dev/null &
    sleep 2
else
    # Host mode: use native Ollama
    if ! pgrep -x "ollama" > /dev/null; then
        echo "Starting local Ollama (bound to 0.0.0.0)..."
        OLLAMA_HOST=0.0.0.0:11434 ollama serve &>/dev/null &
        sleep 3
    else
        echo "Local Ollama already running"
        echo "  Note: Ensure it was started with OLLAMA_HOST=0.0.0.0:11434"
    fi
fi

# Install or upgrade Helm release
echo "Deploying Helm chart..."
if helm status harness -n $NAMESPACE &>/dev/null; then
    helm upgrade harness ./harness-chart -n $NAMESPACE \
        --set harness.ollamaMode=$OLLAMA_MODE \
        --set namespace=$NAMESPACE
else
    helm install harness ./harness-chart -n $NAMESPACE --create-namespace \
        --set harness.ollamaMode=$OLLAMA_MODE \
        --set namespace=$NAMESPACE
fi

# Wait for pods to be ready
echo "Waiting for pods to be ready..."
sleep 5
if [ "$OLLAMA_MODE" = "k8s" ]; then
    kubectl -n $NAMESPACE wait --for=condition=ready pod -l app=ollama --timeout=120s 2>/dev/null || \
        echo "  Ollama still starting..."
fi
kubectl -n $NAMESPACE wait --for=condition=ready pod -l app=qdrant --timeout=120s 2>/dev/null || \
    echo "  Qdrant still starting..."
kubectl -n $NAMESPACE wait --for=condition=ready pod -l app=harness --timeout=120s 2>/dev/null || \
    echo "  Harness still starting..."

# Kill any existing port-forwards for this namespace
pkill -f "kubectl.*port-forward.*$NAMESPACE" 2>/dev/null || true

# Start port forwarding
echo "Starting port forwards..."
if [ "$OLLAMA_MODE" = "k8s" ]; then
    kubectl -n $NAMESPACE port-forward svc/ollama 11434:11434 &>/dev/null &
fi
kubectl -n $NAMESPACE port-forward svc/qdrant 6333:6333 &>/dev/null &

sleep 2

# Verify services
echo ""
echo "Checking services..."

printf "Ollama: "
curl -s http://localhost:11434/api/tags > /dev/null && echo "OK" || echo "FAILED"

printf "Qdrant: "
curl -s http://localhost:6333/collections > /dev/null && echo "OK" || echo "FAILED"

echo ""
echo "Ready! Run 'kubectl -n $NAMESPACE attach -it deployment/harness' to use the agent."
