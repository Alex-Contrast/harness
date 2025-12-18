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

### Build Commands
# Build image
docker build -t harness:local .

# Load into minikube
minikube image load harness:local

# Deploy
kubectl apply -f k8s/harness/

# Attach to agent (interactive)
kubectl -n harness attach -it deployment/harness

# Or run one-off command
kubectl -n harness exec -it deployment/harness -- python -m harness "explain this repo"

# Dynamic (finds pod name for you)
kubectl -n harness cp ~/.ollama/models/blobs $(kubectl -n harness get pods -l app=ollama -o jsonpath='{.items[0].metadata.name}'):/root/.ollama/models/blobs

# Or direct with your pod name
kubectl -n harness cp ~/.ollama/models/blobs ollama-797bf4bdf9-rzdqq:/root/.ollama/models/blobs
kubectl -n harness cp ~/.ollama/models/manifests ollama-797bf4bdf9-rzdqq:/root/.ollama/models/manifests

# Check if Ollama is reachable
kubectl -n harness exec deployment/harness -- python -c "import urllib.request; print(urllib.request.urlopen('http://ollama.harness.svc.cluster.local:11434/api/tags').read().decode())"

# Test model
kubectl -n harness exec deployment/harness -- python -c "
import urllib.request
import json
data = json.dumps({'model': 'codestral:22b-v0.1-q8_0', 'prompt': 'hi', 'stream': False}).encode()
req = urllib.request.Request('http://ollama.harness.svc.cluster.local:11434/api/generate', data=data, headers={'Content-Type': 'application/json'})
print(urllib.request.urlopen(req, timeout=120).read().decode())
"
# watch logs
kubectl -n harness logs -f deployment/harness

# metrics server
minikube addons enable metrics-server
# watch metrics
watch kubectl -n harness top pods

# Check if metrics-server pod is running
kubectl -n kube-system get pods -l k8s-app=metrics-server
kubectl -n kube-system describe pod -l k8s-app=metrics-server

#check minikube
kubectl describe node minikube | grep -A5 "Taints"

# check usage
kubectl -n harness top pods
kubectl -n harness top pods --containers
#| Metric                  | Too Low        | Too High          |
#|-------------------------|----------------|-------------------|
#| Memory usage near limit | OOMKilled risk | Wasting resources |
#| CPU throttled           | Slow responses | Wasting quota     |

# stern to watch logs
stern -n harness .
# <pod-name> <container-name> │ <log message>
```