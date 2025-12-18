#!/bin/bash

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

NAMESPACE=${HELM_NAMESPACE:-harness-helm}

echo "Stopping Harness K8s infrastructure (Helm)..."

# Stop port forwards
echo "Stopping port forwards..."
pkill -f "kubectl.*port-forward.*$NAMESPACE" 2>/dev/null || true

# Stop minikube mount
echo "Stopping minikube mount..."
pkill -f "minikube mount" 2>/dev/null || true

# Uninstall if --full flag is passed
if [[ "$1" == "--full" ]]; then
    echo "Uninstalling Helm release..."
    helm uninstall harness -n $NAMESPACE 2>/dev/null || true

    echo "Deleting namespace..."
    kubectl delete namespace $NAMESPACE 2>/dev/null || true

    echo "Stopping minikube..."
    minikube stop
    echo ""
    echo "Helm release uninstalled and minikube stopped."
elif [[ "$1" == "--uninstall" ]]; then
    echo "Uninstalling Helm release..."
    helm uninstall harness -n $NAMESPACE
    echo ""
    echo "Helm release uninstalled. Cluster still running."
else
    echo ""
    echo "Port forwards and mounts stopped."
    echo "Helm release still deployed. Use:"
    echo "  './stopHelm.sh --uninstall' to remove Helm release"
    echo "  './stopHelm.sh --full' to uninstall and stop minikube"
fi
