# Harness - Local Code Agent (Python + Ollama + Qdrant)

## APP Overview

A minimal, local-first coding agent built in Python using:
- **Ollama** for local LLM inference (Codestral 22B) with native tool calling
- **Qdrant** for semantic search across repos and docs
- **Python** for the agent loop and tools

No frameworks. No API keys. Just `ollama` + `qdrant-client` + ~200 lines of code.

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│                   Python Agent (harness)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐  │
│  │ Agent Loop  │  │   Tools     │  │      Config       │  │
│  │  (~50 LOC)  │  │  (fs, shell)│  │   (config.py)     │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────────────┘  │
└─────────┼────────────────┼────────────────────────────────┘
          │                │
          ▼                ▼
┌───────────────────────────────────┐  ┌─────────────────┐
│       ollama (Python client)      │  │  qdrant-client  │
│                                   │  │                 │
│  ┌─────────────┐ ┌──────────────┐ │  │  ┌───────────┐  │
│  │ Codestral   │ │ nomic-embed  │ │  │  │  Vectors  │  │
│  │ (chat+tools)│ │ (embeddings) │ │  │  │  + Code   │  │
│  └─────────────┘ └──────────────┘ │  │  └───────────┘  │
└───────────────────────────────────┘  └─────────────────┘
          │                                    │
          ▼                                    ▼
   localhost:11434                      localhost:6333
```

**Key simplification:** Official Python clients handle all HTTP/streaming complexity. Native tool calling means no response parsing - just check `response.message.tool_calls`.

---

## Phase 1: Python Agent Core

### Goal
Working code agent in Python with native tool calling via Ollama.

### Stack
| Component | Library |
|-----------|---------|
| LLM | `ollama` (official Python client) |
| Vector DB | `qdrant-client` |
| Config | `pydantic` (optional, or just dataclass) |

### Project Structure
```
harness/
├── harness/
│   ├── __init__.py
│   ├── __main__.py       # Entry point: python -m harness
│   ├── config.py         # Settings
│   ├── agent.py          # Agent loop (~50 lines)
│   └── tools/
│       ├── __init__.py
│       ├── base.py       # Tool base class
│       ├── file.py       # read, write, list
│       ├── shell.py      # run commands
│       └── search.py     # grep/find
├── pyproject.toml
├── start.sh
├── stop.sh
└── plan.md
```

### Tasks
- [ ] Set up Python project with pyproject.toml
- [ ] Define config (models, limits, settings)
- [ ] Define tool base class and tool definitions
- [ ] Implement file tools (read, write, list directory)
- [ ] Implement shell tool (run commands)
- [ ] Build agent loop (native tool_calls)
- [ ] Add streaming output
- [ ] Add REPL interface
- [ ] Test with Codestral 22B

### Config
```python
# config.py
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class Config:
    chat_model: str = "codestral"
    embed_model: str = "nomic-embed-text"
    max_steps: int = 20
    max_context_tokens: int = 28000  # Leave headroom in 32k window
    stream: bool = True

    @classmethod
    def load(cls) -> "Config":
        config_path = Path.home() / ".harness" / "config.json"
        if config_path.exists():
            return cls(**json.loads(config_path.read_text()))
        return cls()
```

### Tool Definitions
```python
# tools/base.py
from abc import ABC, abstractmethod
from typing import Any

class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool and return result as string."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """Return JSON schema for parameters."""
        pass

    def to_definition(self) -> dict:
        """Convert to Ollama tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

# tools/file.py
class ReadFileTool(Tool):
    name = "read_file"
    description = "Read contents of a file at the given path"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path to the file"}
            },
            "required": ["path"]
        }

    def execute(self, path: str) -> str:
        try:
            return Path(path).read_text()
        except Exception as e:
            return f"Error: {e}"
```

### Agent Loop
```python
# agent.py
import ollama
import json
from config import Config
from tools import TOOLS  # dict of name -> Tool instance

config = Config.load()

SYSTEM_PROMPT = """You are a coding assistant with access to tools.
Use tools to read files, run commands, and search code.
Always use absolute paths. Be concise."""

def run(task: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task}
    ]

    tool_definitions = [t.to_definition() for t in TOOLS.values()]

    for _ in range(config.max_steps):
        response = ollama.chat(
            model=config.chat_model,
            messages=messages,
            tools=tool_definitions,
            stream=False
        )

        msg = response.message

        # Check for tool calls
        if msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content, "tool_calls": msg.tool_calls})

            for call in msg.tool_calls:
                name = call.function.name
                args = call.function.arguments  # Already a dict

                if name in TOOLS:
                    result = TOOLS[name].execute(**args)
                else:
                    result = f"Unknown tool: {name}"

                messages.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": call.id if hasattr(call, 'id') else name
                })
        else:
            # No tool calls = final response
            return msg.content

    return "Max steps reached"
```

### Streaming Output
```python
# For better UX, stream the final response
def run_streaming(task: str):
    # ... same setup ...

    for _ in range(config.max_steps):
        # Non-streaming for tool calls
        response = ollama.chat(model=config.chat_model, messages=messages, tools=tool_definitions)

        if response.message.tool_calls:
            # Handle tools (same as above)
            pass
        else:
            # Stream final response
            stream = ollama.chat(
                model=config.chat_model,
                messages=messages,
                stream=True
            )
            for chunk in stream:
                print(chunk.message.content, end="", flush=True)
            print()
            return
```

### REPL Interface
```python
# __main__.py
from agent import run

def main():
    print("Harness - Local Code Agent")
    print("Type 'quit' to exit\n")

    while True:
        try:
            task = input(">>> ").strip()
            if task.lower() in ("quit", "exit"):
                break
            if not task:
                continue

            result = run(task)
            print(f"\n{result}\n")
        except KeyboardInterrupt:
            print("\nInterrupted")
            break

if __name__ == "__main__":
    main()
```

---

## Phase 2: Qdrant Integration

### Goal
Semantic search across repos and documents.

### Stack
| Component | Tech |
|-----------|------|
| Vector DB | Qdrant (Docker) via `qdrant-client` |
| Embeddings | Ollama (nomic-embed-text) via `ollama.embed()` |

### Tasks

#### 2a: Qdrant Setup
- [ ] Run Qdrant via Docker (already in start.sh)
- [ ] Create collections for code and docs

#### 2b: Embedding Pipeline
- [ ] Pull embedding model: `ollama pull nomic-embed-text`
- [ ] Build indexer for code files
- [ ] Build indexer for documents
- [ ] Chunking strategy (functions/classes for code, sections for docs)

#### 2c: Search Tool
- [ ] Add SemanticSearchTool to agent tools
- [ ] Test search queries

### Qdrant Setup
```python
# qdrant_setup.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(host="localhost", port=6333)

# Create collection for code (nomic-embed-text produces 768-dim vectors)
client.create_collection(
    collection_name="code",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
)
```

### Indexing Code
```python
# indexer.py
import ollama
from pathlib import Path
from qdrant_client.models import PointStruct

def chunk_file(path: Path) -> list[dict]:
    """Split file into chunks with metadata."""
    content = path.read_text()
    # Simple chunking: ~500 lines or by function (can improve later)
    return [{
        "content": content[:2000],  # Start simple
        "path": str(path),
        "language": path.suffix
    }]

def index_directory(directory: str):
    points = []
    for path in Path(directory).rglob("*.py"):  # Add more patterns
        for i, chunk in enumerate(chunk_file(path)):
            # Get embedding from Ollama
            embedding = ollama.embed(
                model="nomic-embed-text",
                input=chunk["content"]
            )["embeddings"][0]

            points.append(PointStruct(
                id=hash(f"{path}:{i}"),
                vector=embedding,
                payload=chunk
            ))

    client.upsert(collection_name="code", points=points)
```

### Search Tool
```python
# tools/search.py
import ollama
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

class SemanticSearchTool(Tool):
    name = "semantic_search"
    description = "Search codebase for relevant code using natural language"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language search query"}
            },
            "required": ["query"]
        }

    def execute(self, query: str) -> str:
        # Embed the query
        embedding = ollama.embed(model="nomic-embed-text", input=query)["embeddings"][0]

        # Search Qdrant
        results = client.query_points(
            collection_name="code",
            query=embedding,
            limit=5
        )

        # Format results
        output = []
        for r in results.points:
            output.append(f"## {r.payload['path']}\n```\n{r.payload['content'][:500]}...\n```")

        return "\n\n".join(output) if output else "No results found"
```

### Chunking Strategy
| Content | Chunk By | Metadata |
|---------|----------|----------|
| Python/Code | Function/class (or ~100 lines) | filepath, language |
| Markdown | ## sections | filepath, title |
| Other docs | ~500 tokens | filepath, type |

---

## Phase 3: Polish

### Tasks
- [ ] Error handling and retries (Ollama connection, tool failures)
- [ ] Conversation history (persist across sessions)
- [ ] Context window management (truncate old tool results)
- [ ] Better chunking (AST-based for Python files)
- [ ] Multi-file edit support

---

## File Structure (Final)

```
harness/
├── harness/
│   ├── __init__.py
│   ├── __main__.py           # Entry point
│   ├── config.py             # Settings
│   ├── agent.py              # Agent loop
│   └── tools/
│       ├── __init__.py       # TOOLS registry
│       ├── base.py           # Tool base class
│       ├── file.py           # read, write, list
│       ├── shell.py          # run commands
│       └── search.py         # semantic search (Qdrant)
├── scripts/
│   └── index.py              # Index codebase into Qdrant
├── pyproject.toml
├── start.sh
├── stop.sh
└── plan.md
```

---

## Dependencies

### Python
```toml
# pyproject.toml
[project]
name = "harness"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "ollama",
    "qdrant-client",
]

[project.scripts]
harness = "harness.__main__:main"
```

### System
- macOS with Apple Silicon (or any system with Ollama support)
- [Ollama](https://ollama.com) installed
- Docker (for Qdrant)
- ~16GB+ unified memory (Codestral 22B fits comfortably)
- Python 3.11+

---

## Getting Started

```bash
# 1. Install Ollama (if not already)
brew install ollama

# 2. Pull models
ollama pull codestral
ollama pull nomic-embed-text

# 3. Start services
./start.sh

# 4. Install Python package
pip install -e .

# 5. Run agent
python -m harness
# or after install:
harness
```

---

## Why Python?

1. **Official clients** - `ollama` and `qdrant-client` handle all HTTP/streaming edge cases
2. **Minimal code** - Agent loop is ~50 lines, not ~500
3. **Fast iteration** - No compile step, instant feedback
4. **Rich ecosystem** - If you need something, it exists
5. **Runtime overhead is negligible** - Python just orchestrates; Ollama/Qdrant do the heavy lifting

---

## Open Questions

1. **Embedding model** - Start with nomic-embed-text (768 dims), consider mxbai-embed-large if quality matters more
2. **Chunking** - Simple line-based first, AST-based later for better semantic boundaries
3. **UI** - CLI first, consider textual TUI or web UI later if needed
