### Commands Cheatsheet
```bash
#Run to start the agent.
python -m harness

# Dry run commands to check syntax
kubectl apply -f k8s/namespace.yml --dry-run=client
kubectl apply -f k8s/ollama/ --dry-run=client
kubectl apply -f k8s/qdrant/ --dry-run=client

# Deploy
# 1. Start minikube (if not running)
minikube start --cpus=4 --memory=12g

# 2. Apply manifests (for real this time)
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/ollama/
kubectl apply -f k8s/qdrant/

# 3. Watch pods come up
kubectl -n harness get pods -w

# Stop
minikube stop
# OR remove cluster and data: minikube delete

# Get pod name
kubectl -n harness get pods -l app=ollama -o name
# Verify ollama depoyment is available
kubectl -n harness exec deployment/ollama -- ollama list
#Files might not have persisted to the PVC. Let's check:
kubectl -n harness exec deployment/ollama -- ls -la /root/.ollama/
kubectl -n harness exec deployment/ollama -- ls -la /root/.ollama/models/
#Also check if the PVC is mounted correctly:
kubectl -n harness exec deployment/ollama -- df -h /root/.ollama

# Test connectivity:
# Ollama
curl http://localhost:11434/api/tags
# Qdrant
curl http://localhost:6333/collections

# Apply all manifests
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/ollama/
kubectl apply -f k8s/qdrant/

# Check status
kubectl -n harness get pods
kubectl -n harness get pvc
kubectl -n harness get all

# Port forward to access from host
kubectl -n harness port-forward svc/ollama 11434:11434 &
kubectl -n harness port-forward svc/qdrant 6333:6333 &

# Pull model (exec into ollama pod)
kubectl -n harness exec -it deployment/ollama -- ollama pull codestral
kubectl -n harness exec -it deployment/ollama -- ollama pull nomic-embed-text

# View logs
kubectl -n harness logs -f deployment/ollama
kubectl -n harness logs -f statefulset/qdrant

# Cleanup
kubectl delete namespace harness
```