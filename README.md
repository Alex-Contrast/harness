# Harness

A local-first coding agent built with Python, Ollama, and Kubernetes.
Just building something simple to learn K8s.

## Overview

Harness is a minimal coding assistant that runs entirely on your machine:
- **Ollama** for LLM inference (Codestral 22B)
- **Qdrant** for semantic search (planned)
- **Kubernetes** (minikube) for orchestration
- **MCP** for tool integration

## Requirements

- macOS with Apple Silicon (or Linux)
- Python 3.11+
- Docker
- minikube & kubectl
- helm (optional, for Helm deployment)

## Quick Start

```bash
# Install tools (macOS)
brew install minikube kubectl

# Install Python package
pip install -e .

# Start infrastructure
./start.sh

# Run agent
python -m harness

# with k8s
kubectl -n harness attach -it deployment/harness
# to quit interactive mode -- /quit
```

## Scripts

### kubectl-based (manual manifests)
| Script | Description |
|--------|-------------|
| `./start.sh` | Start minikube, deploy services, set up port-forwarding |
| `./stop.sh` | Stop port-forwards (cluster keeps running) |
| `./stop.sh --full` | Stop port-forwards and minikube |
| `./run-job.sh "task"` | Run a one-shot agent task as K8s Job |

### Helm-based (packaged chart)
| Script | Description |
|--------|-------------|
| `./startHelm.sh` | Deploy via Helm chart to `harness-helm` namespace |
| `./stopHelm.sh` | Stop port-forwards |
| `./stopHelm.sh --uninstall` | Uninstall Helm release |
| `./stopHelm.sh --full` | Uninstall and stop minikube |
| `./runHelm-job.sh "task"` | Run task in Helm namespace |

## Project Structure

```
harness/
├── harness/           # Python agent
├── k8s/               # Kubernetes manifests (kubectl)
│   ├── namespace.yml
│   ├── ollama/        # LLM service (k8s mode only)
│   ├── qdrant/        # Vector DB
│   ├── harness/       # Agent deployment + configmaps
│   └── jobs/          # Job templates
├── harness-chart/     # Helm chart
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/     # Templated K8s manifests
├── Dockerfile
├── start.sh / startHelm.sh
├── stop.sh / stopHelm.sh
└── .env               # Environment config
```

## Helm Deployment

The Helm chart packages all K8s resources with configurable values:

```bash
# Install
brew install helm

# Deploy (creates harness-helm namespace)
./startHelm.sh

# Or manually
helm install harness ./harness-chart --create-namespace -n harness-helm

# Customize values
helm install harness ./harness-chart -n harness-helm \
  --set harness.ollamaMode=k8s \
  --set ollama.resources.limits.memory=32Gi

# Upgrade after changes
helm upgrade harness ./harness-chart -n harness-helm

# Uninstall
helm uninstall harness -n harness-helm
```

### Helm vs kubectl

| Approach | Pros | Cons |
|----------|------|------|
| kubectl + manifests | Simple, explicit | Manual tracking, no versioning |
| Helm chart | Versioned, configurable, rollback | Extra abstraction |

## Configuration

Environment variables (`.env`):
```bash
# Minikube resources
MINIKUBE_MEMORY=24g
MINIKUBE_CPUS=4

# Ollama mode: "host" (native, fast) or "k8s" (containerized, slower)
OLLAMA_MODE=host

# Service endpoints (for local dev without K8s)
OLLAMA_HOST=0.0.0.0:11434
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### Ollama Modes

| Mode | Description | Performance |
|------|-------------|-------------|
| `host` | Native Ollama on Mac, Harness+Qdrant in K8s | Fast |
| `k8s` | Everything containerized in K8s | Slower, but fully orchestrated |

## REPL Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/tools` | List available MCP tools |
| `/context` | Show conversation stats |
| `/clear` | Clear conversation history |
| `/quit` | Exit |

## Architecture

### Host Mode (OLLAMA_MODE=host) - Recommended
```
┌─────────────────────────────────────────┐
│  Your Mac                               │
│                                         │
│  ┌─────────────────┐                    │
│  │ Ollama (native) │ ← Fast, full HW    │
│  │ 0.0.0.0:11434   │                    │
│  └────────┬────────┘                    │
│           │                             │
│  ┌────────┼─────────────────────────┐   │
│  │  K8s   │                         │   │
│  │        ▼                         │   │
│  │  ┌──────────┐    ┌─────────┐     │   │
│  │  │ Harness  │───▶│ Qdrant  │     │   │
│  │  └──────────┘    └─────────┘     │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### K8s Mode (OLLAMA_MODE=k8s) - Full Containerization
```
┌─────────────────────────────────────────┐
│  Your Mac                               │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │  Minikube (K8s)                  │   │
│  │                                  │   │
│  │  ┌─────────┐  ┌─────────┐        │   │
│  │  │ Ollama  │  │ Qdrant  │        │   │
│  │  │ :11434  │  │ :6333   │        │   │
│  │  └────┬────┘  └────┬────┘        │   │
│  │       │            │             │   │
│  │       ▼            ▼             │   │
│  │      ┌──────────────┐            │   │
│  │      │   Harness    │            │   │
│  │      └──────────────┘            │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```
