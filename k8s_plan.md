# Harness K8s Infrastructure Plan

## Overview

Use Kubernetes to orchestrate the Harness local AI stack, learning K8s concepts through practical application.

### Component Mapping

| Component     | K8s Resource              | Why                                                        |
|---------------|---------------------------|------------------------------------------------------------|
| Ollama        | Deployment + Service      | Stateless (models loaded from disk), needs resource limits |
| Qdrant        | StatefulSet + PVC         | Needs persistent storage for vectors                       |
| Harness agent | Deployment / Job          | Stateless, talks to other services via DNS                 |
| Indexing      | Job / CronJob             | Run-to-completion workloads                                |
| Config        | ConfigMap + Secret        | Model names, endpoints, decouple config from code          |

### K8s Concepts Covered

| Concept | Where You'll Use It |
|---------|---------------------|
| Namespaces | Isolate harness stack from other experiments |
| Deployments | Ollama, Harness agent |
| StatefulSets | Qdrant (stable network identity + storage) |
| Services (ClusterIP) | Internal DNS: `ollama.harness.svc.cluster.local` |
| PersistentVolumeClaims | Qdrant vector storage, Ollama model cache |
| ConfigMaps | Model names, embedding dimensions, endpoints |
| Secrets | API keys (if any), sensitive config |
| Jobs | One-off indexing tasks |
| CronJobs | Scheduled reindexing |
| Resource limits/requests | Prevent Ollama from starving the system |
| Probes (readiness/liveness) | Wait for Ollama model load, health checks |
| kubectl | CLI interaction with cluster |

---

## Prerequisites

### Install Tools
```bash
# macOS
brew install minikube kubectl

# Verify
minikube version
kubectl version --client
```

### Start Cluster
```bash
# Start minikube with enough resources for Ollama
minikube start \
  --cpus=4 \
  --memory=12g \
  --driver=docker

# Verify
kubectl cluster-info
kubectl get nodes
```

### Project Structure
```
harness/
├── k8s/
│   ├── namespace.yaml
│   ├── ollama/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── pvc.yaml           # Model cache persistence
│   ├── qdrant/
│   │   ├── statefulset.yaml
│   │   └── service.yaml
│   ├── harness/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   └── jobs/
│       ├── index-job.yaml
│       └── index-cronjob.yaml
├── harness/                    # Python agent code
├── Dockerfile                  # For Phase 2+
└── k8s_plan.md
```

---

## Phase 1: Infrastructure Foundation

**Goal**: Get Ollama and Qdrant running in K8s, agent runs locally and connects to cluster.

### Tasks

- [x] Create k8s/ directory structure
- [x] Create harness namespace
- [x] Deploy Ollama
  - [x] Deployment with resource limits
  - [x] Service (ClusterIP)
  - [x] PVC for model cache (optional but recommended)
- [x] Deploy Qdrant
  - [x] StatefulSet with PVC
  - [x] Service (ClusterIP)
- [x] Expose services to host (minikube tunnel or port-forward)
- [x] Update harness config to use K8s endpoints
- [x] Test: agent can reach Ollama and Qdrant

### Manifests

#### Namespace
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: harness
```

#### Ollama
```yaml
# k8s/ollama/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
  namespace: harness
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "10Gi"
            cpu: "4"
        volumeMounts:
        - name: ollama-data
          mountPath: /root/.ollama
      volumes:
      - name: ollama-data
        persistentVolumeClaim:
          claimName: ollama-pvc
---
# k8s/ollama/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ollama-pvc
  namespace: harness
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi  # Models are large
---
# k8s/ollama/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ollama
  namespace: harness
spec:
  selector:
    app: ollama
  ports:
  - port: 11434
    targetPort: 11434
```

#### Qdrant
```yaml
# k8s/qdrant/statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: qdrant
  namespace: harness
spec:
  serviceName: qdrant
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:latest
        ports:
        - containerPort: 6333
        - containerPort: 6334
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1"
        volumeMounts:
        - name: qdrant-storage
          mountPath: /qdrant/storage
  volumeClaimTemplates:
  - metadata:
      name: qdrant-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
# k8s/qdrant/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: qdrant
  namespace: harness
spec:
  selector:
    app: qdrant
  ports:
  - name: http
    port: 6333
    targetPort: 6333
  - name: grpc
    port: 6334
    targetPort: 6334
```

### Commands Cheatsheet
```bash
# Apply all manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/ollama/
kubectl apply -f k8s/qdrant/

# Check status
kubectl -n harness get pods
kubectl -n harness get pvc

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

---

## Phase 2: Agent in Cluster

**Goal**: Run Harness agent inside K8s, all communication stays in-cluster.

### Tasks

- [x] Create Dockerfile for harness agent
- [x] Build and load image into minikube
- [x] Create ConfigMap for agent settings
- [x] Create Deployment for harness agent
- [x] Update agent code to read config from environment/ConfigMap
- [x] Test: agent runs in cluster, uses internal DNS

### Dockerfile
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY harness/ harness/

# Use environment variables for config
ENV OLLAMA_HOST=ollama.harness.svc.cluster.local:11434
ENV QDRANT_HOST=qdrant.harness.svc.cluster.local
ENV QDRANT_PORT=6333

CMD ["python", "-m", "harness"]
```

### ConfigMap
```yaml
# k8s/harness/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: harness-config
  namespace: harness
data:
  OLLAMA_HOST: "ollama.harness.svc.cluster.local:11434"
  QDRANT_HOST: "qdrant.harness.svc.cluster.local"
  QDRANT_PORT: "6333"
  CHAT_MODEL: "codestral"
  EMBED_MODEL: "nomic-embed-text"
```

### Deployment
```yaml
# k8s/harness/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: harness
  namespace: harness
spec:
  replicas: 1
  selector:
    matchLabels:
      app: harness
  template:
    metadata:
      labels:
        app: harness
    spec:
      containers:
      - name: harness
        image: harness:local
        imagePullPolicy: Never  # Use local image
        envFrom:
        - configMapRef:
            name: harness-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        stdin: true
        tty: true
```

### Build Commands
```bash
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
```

---

## Phase 3: Production Patterns

**Goal**: Add reliability features - probes, proper resource tuning, observability.

### Tasks

- [x] Add readiness probe to Ollama (wait for model load)
- [x] Add liveness probes to all services
- [x] Tune resource limits based on actual usage
- [x] Add pod disruption budgets (optional)
- [-] Set up basic logging aggregation (optional) --> using stern for observability

### Ollama Probes
```yaml
# Add to ollama deployment spec.containers[]
readinessProbe:
  httpGet:
    path: /api/tags  # Returns loaded models
    port: 11434
  initialDelaySeconds: 30  # Models take time to load
  periodSeconds: 10
  timeoutSeconds: 5
livenessProbe:
  httpGet:
    path: /api/tags
    port: 11434
  initialDelaySeconds: 60
  periodSeconds: 30
```

### Qdrant Probes
```yaml
# Add to qdrant statefulset spec.containers[]
readinessProbe:
  httpGet:
    path: /readyz
    port: 6333
  initialDelaySeconds: 5
  periodSeconds: 10
livenessProbe:
  httpGet:
    path: /livez
    port: 6333
  initialDelaySeconds: 10
  periodSeconds: 30
```

---

## Phase 4: Job-Based Agent

**Goal**: Run agent as K8s Job per task - more cloud-native pattern.

### Why This Pattern?
- **Resource efficiency**: Pod only exists while task runs
- **Natural isolation**: Each task gets fresh environment
- **Audit trail**: Job history shows what ran and when
- **Scalability**: Multiple jobs can run in parallel

### Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  API/CLI    │────▶│  K8s API    │
│  (request)  │     │ (creates)   │     │ (schedules) │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌──────────────────────────┘
                    ▼
              ┌───────────┐
              │ Agent Job │───▶ Ollama Service
              │  (runs)   │───▶ Qdrant Service
              └─────┬─────┘
                    │
                    ▼
              ┌───────────┐
              │  Results  │
              │(logs/PVC) │
              └───────────┘
```

### Tasks

- [x] Create Job template for agent tasks
- [x] Build simple API/CLI to create jobs
- [x] Handle job output (logs or PVC)
- [x] Add job cleanup policy (TTL)
- [] Test parallel job execution

### Job Template
```yaml
# k8s/jobs/agent-job-template.yaml
apiVersion: batch/v1
kind: Job
metadata:
  generateName: harness-task-
  namespace: harness
spec:
  ttlSecondsAfterFinished: 3600  # Cleanup after 1 hour
  backoffLimit: 1
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: harness
        image: harness:local
        imagePullPolicy: Never
        envFrom:
        - configMapRef:
            name: harness-config
        env:
        - name: HARNESS_TASK
          value: "{{TASK}}"  # Replaced when creating job
        command: ["python", "-m", "harness", "--task", "$(HARNESS_TASK)"]
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Job Runner Script
```bash
#!/bin/bash
# scripts/run-task.sh
TASK="$1"

kubectl -n harness create job \
  --from=job/harness-task-template \
  harness-task-$(date +%s) \
  -- python -m harness --task "$TASK"

# Or using envsubst with template
# TASK="$1" envsubst < k8s/jobs/agent-job-template.yaml | kubectl apply -f -
```

---

## Phase 5: Automation & Workflows -- Skipping to 6 to learn about helm

**Goal**: Scheduled indexing, automated maintenance, optional n8n for visual workflows.

### Tasks

- [ ] Create CronJob for scheduled reindexing
- [ ] Create Job for on-demand indexing
- [ ] (Optional) Deploy n8n for visual workflows
- [ ] (Optional) Set up webhook endpoint for git-triggered indexing

### Index CronJob
```yaml
# k8s/jobs/index-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: reindex
  namespace: harness
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: indexer
            image: harness:local
            imagePullPolicy: Never
            envFrom:
            - configMapRef:
                name: harness-config
            command: ["python", "-m", "harness.indexer"]
            volumeMounts:
            - name: repos
              mountPath: /repos
              readOnly: true
          volumes:
          - name: repos
            hostPath:
              path: /Users/alexcorll/dev  # Mount host repos
              type: Directory
```

### On-Demand Index Job
```yaml
# k8s/jobs/index-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: index-now
  namespace: harness
spec:
  ttlSecondsAfterFinished: 300
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: indexer
        image: harness:local
        imagePullPolicy: Never
        envFrom:
        - configMapRef:
            name: harness-config
        command: ["python", "-m", "harness.indexer", "--path", "/repos"]
        volumeMounts:
        - name: repos
          mountPath: /repos
          readOnly: true
      volumes:
      - name: repos
        hostPath:
          path: /Users/alexcorll/dev
          type: Directory
```

### n8n (Optional)
```yaml
# k8s/n8n/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: n8n
  namespace: harness
spec:
  replicas: 1
  selector:
    matchLabels:
      app: n8n
  template:
    metadata:
      labels:
        app: n8n
    spec:
      containers:
      - name: n8n
        image: n8nio/n8n:latest
        ports:
        - containerPort: 5678
        env:
        - name: WEBHOOK_URL
          value: "http://localhost:5678"
        volumeMounts:
        - name: n8n-data
          mountPath: /home/node/.n8n
      volumes:
      - name: n8n-data
        persistentVolumeClaim:
          claimName: n8n-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: n8n
  namespace: harness
spec:
  selector:
    app: n8n
  ports:
  - port: 5678
    targetPort: 5678
```

### n8n Workflow Ideas
1. **Git webhook → Reindex**: Receive webhook, trigger index job via K8s API
2. **Nightly backup**: Snapshot Qdrant, store to local volume
3. **Health dashboard**: Poll services, alert on failure
4. **Model updater**: Weekly check for new Ollama model versions

---

## Phase 6: Helm Chart (Optional)

**Goal**: Package everything for easy deployment and sharing.

### Tasks

- [x] Initialize Helm chart structure
- [x] Templatize all manifests
- [x] Add values.yaml for customization
- [x] Document installation

### Structure
```
harness-chart/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── namespace.yaml
│   ├── ollama-deployment.yaml
│   ├── ollama-service.yaml
│   ├── ollama-pvc.yaml
│   ├── qdrant-statefulset.yaml
│   ├── qdrant-service.yaml
│   ├── harness-deployment.yaml
│   ├── harness-configmap.yaml
│   └── _helpers.tpl
└── README.md
```

### values.yaml
```yaml
namespace: harness

ollama:
  image: ollama/ollama:latest
  resources:
    requests:
      memory: "4Gi"
      cpu: "2"
    limits:
      memory: "10Gi"
      cpu: "4"
  storage: 50Gi
  models:
    - codestral
    - nomic-embed-text

qdrant:
  image: qdrant/qdrant:latest
  resources:
    requests:
      memory: "512Mi"
    limits:
      memory: "2Gi"
  storage: 10Gi

harness:
  image: harness:local
  chatModel: codestral
  embedModel: nomic-embed-text
```

---

## Quick Reference

### Common Commands
```bash
# Start cluster
minikube start --cpus=4 --memory=12g

# Deploy everything
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/ollama/
kubectl apply -f k8s/qdrant/

# Port forward (background)
kubectl -n harness port-forward svc/ollama 11434:11434 &
kubectl -n harness port-forward svc/qdrant 6333:6333 &

# Check status
kubectl -n harness get all
kubectl -n harness get pvc

# Pull models
kubectl -n harness exec -it deploy/ollama -- ollama pull codestral

# View logs
kubectl -n harness logs -f deploy/ollama

# Run indexing job
kubectl -n harness apply -f k8s/jobs/index-job.yaml

# Cleanup
minikube stop
# or full delete:
minikube delete
```

### Troubleshooting
```bash
# Pod not starting?
kubectl -n harness describe pod <pod-name>

# Check events
kubectl -n harness get events --sort-by='.lastTimestamp'

# Shell into pod
kubectl -n harness exec -it deploy/ollama -- /bin/sh

# Check resource usage
kubectl -n harness top pods

# PVC stuck?
kubectl -n harness get pvc
kubectl -n harness describe pvc <pvc-name>
```

---