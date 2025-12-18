#!/bin/bash

echo "Starting Harness K8s infrastructure..."

# Start minikube if not running
if ! minikube status | grep -q "Running"; then
    echo "Starting minikube..."
    minikube start --cpus=4 --memory=12g
else
    echo "Minikube already running"
fi

# Apply K8s manifests
echo "Applying K8s manifests..."
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/ollama/
kubectl apply -f k8s/qdrant/

# Wait for pods to be ready
echo "Waiting for pods to be ready..."
kubectl -n harness wait --for=condition=ready pod -l app=ollama --timeout=120s
kubectl -n harness wait --for=condition=ready pod -l app=qdrant --timeout=120s

# Kill any existing port-forwards
pkill -f "kubectl.*port-forward.*harness" 2>/dev/null || true

# Start port forwarding in background
echo "Starting port forwards..."
kubectl -n harness port-forward svc/ollama 11434:11434 &>/dev/null &
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
echo "Ready! Run 'python -m harness' to start the agent."
