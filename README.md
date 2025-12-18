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

| Script | Description |
|--------|-------------|
| `./start.sh` | Start minikube, deploy services, set up port-forwarding |
| `./stop.sh` | Stop port-forwards (cluster keeps running) |
| `./stop.sh --full` | Stop port-forwards and minikube |

## Project Structure

```
harness/
├── harness/           # Python agent
├── k8s/               # Kubernetes manifests
│   ├── namespace.yml
│   ├── ollama/        # LLM service (k8s mode only)
│   ├── qdrant/        # Vector DB
│   └── harness/       # Agent deployment + configmaps
├── Dockerfile
├── start.sh
├── stop.sh
└── .env               # Environment config
```

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
