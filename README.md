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
│   ├── ollama/        # LLM service
│   └── qdrant/        # Vector DB
├── start.sh
├── stop.sh
└── .env               # Environment config
```

## Configuration

Environment variables (`.env`):
```
OLLAMA_HOST=http://localhost:11434
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

## REPL Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/tools` | List available MCP tools |
| `/context` | Show conversation stats |
| `/clear` | Clear conversation history |
| `/quit` | Exit |

## Architecture

```
┌─────────────────────────────────────────┐
│  Your Machine                           │
│                                         │
│  ┌───────────┐     port-forward         │
│  │  Harness  │◄────────────────────┐    │
│  │  (Python) │                     │    │
│  └───────────┘                     │    │
│                                    │    │
│  ┌─────────────────────────────────┼──┐ │
│  │  Minikube (K8s)                 │  │ │
│  │                                 │  │ │
│  │  ┌─────────┐    ┌─────────┐     │  │ │
│  │  │ Ollama  │    │ Qdrant  │◄───-┘  │ │
│  │  │ :11434  │    │ :6333   │        │ │
│  │  └─────────┘    └─────────┘        │ │
│  │                                    │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```
