#!/bin/bash

echo "Stopping Harness K8s infrastructure..."

# Stop port forwards
echo "Stopping port forwards..."
pkill -f "kubectl.*port-forward.*harness" 2>/dev/null || true

# Full stop if --full flag is passed
if [[ "$1" == "--full" ]]; then
    echo "Stopping minikube..."
    minikube stop
    echo ""
    echo "Minikube stopped."
else
    echo ""
    echo "Port forwards stopped."
    echo "Cluster still running. Use './stop.sh --full' to stop minikube."
fi
