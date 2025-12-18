# Harness Usage Guide

A local code agent powered by Ollama and Qdrant.

## Quick Start

```bash
# Start services (Ollama + Qdrant)
./start.sh

# Run interactive REPL
python -m harness

# Or run a single command
python -m harness "list files in /path/to/dir"
```

## Installation

```bash
# Install dependencies
pip install -e .

# Pull the model
ollama pull codestral:22b-v0.1-q8_0
```

## Modes

### Interactive REPL (Recommended)

```bash
python -m harness
```

Starts an interactive session with persistent context. The agent remembers previous turns until you clear.

```
Harness - Local Code Agent
Model: codestral:22b-v0.1-q8_0
Type /help for commands

>>> Read the file config.py
  -> read_file(path='config.py')
[agent shows file analysis]

>>> What does the Config class do?
[agent answers using context - no tool call needed]

>>> /clear
Context cleared.
```

### One-Shot Mode

```bash
python -m harness "your task here"
```

Runs a single task and exits. No context persistence.

```bash
python -m harness "list files in /Users/me/project"
python -m harness "read /path/to/file.py and explain it"
python -m harness "run git status in /path/to/repo"
```

## REPL Commands

All commands start with `/`:

| Command    | Description                              |
|------------|------------------------------------------|
| `/help`    | Show help and examples                   |
| `/clear`   | Clear conversation context (start fresh) |
| `/context` | Show context stats (messages, tokens)    |
| `/history` | Show recent conversation history         |
| `/config`  | Show current configuration               |
| `/quit`    | Exit the REPL (also: `/exit`, `/q`)      |

### /context

Shows current session stats:

```
>>> /context
  Messages: 7
  Your inputs: 2
  Tool calls: 1
  Est. tokens: ~429
```

Use this to monitor context window usage. Clear when approaching limits.

### /clear

Resets the conversation:

```
>>> /clear
Context cleared.
```

Use when:
- Switching to a different task/project
- Context is getting too large
- Agent is confused by prior context

### /history

Shows recent messages:

```
>>> /history
--- Recent History ---
[You] Read the file config.py
[Agent] The config.py file contains...
[You] What does the Config class do?
[Agent] The Config class is responsible for...
---
```

## Available Tools

The agent has access to these tools:

### read_file
Read contents of a file.

```
>>> Read /path/to/file.py
  -> read_file(path='/path/to/file.py')
```

### write_file
Write content to a file (creates or overwrites).

```
>>> Write "hello world" to /tmp/test.txt
  -> write_file(path='/tmp/test.txt', content='hello world')
```

### list_directory
List files and directories.

```
>>> List the contents of /path/to/dir
  -> list_directory(path='/path/to/dir')
```

### run_command
Execute shell commands.

```
>>> Run git status in /path/to/repo
  -> run_command(command='git status', cwd='/path/to/repo')
```

**Note:** Some dangerous commands are blocked for safety.

## Configuration

Config is stored in `~/.harness/config.json`:

```json
{
  "chat_model": "codestral:22b-v0.1-q8_0",
  "embed_model": "nomic-embed-text",
  "max_steps": 20,
  "max_context_tokens": 28000,
  "stream": true
}
```

### Options

| Option              | Default                    | Description                          |
|---------------------|----------------------------|--------------------------------------|
| `chat_model`        | `codestral:22b-v0.1-q8_0`  | Ollama model for chat                |
| `embed_model`       | `nomic-embed-text`         | Ollama model for embeddings          |
| `max_steps`         | `20`                       | Max tool calls per task              |
| `max_context_tokens`| `28000`                    | Context window limit                 |
| `stream`            | `true`                     | Stream responses (currently unused)  |

## Service Management

### start.sh

Starts Ollama and Qdrant:

```bash
./start.sh
```

Output:
```
Starting Harness dependencies...
Ollama already running
Qdrant already running

Checking services...
Ollama: OK
Qdrant: OK

Ready! Run 'python -m harness' to start the agent.
```

### stop.sh

Stops both services:

```bash
./stop.sh
```

## Examples

### Code Exploration

```
>>> List the files in /Users/me/project/src
  -> list_directory(...)

>>> Read the main.py file
  -> read_file(...)

>>> What does the process_data function do?
[answers from context]

>>> Are there any potential bugs?
[analyzes from context]
```

### Git Operations

```
>>> Run git status in /Users/me/project
  -> run_command(command='git status', cwd='...')

>>> Run git log --oneline -5 in /Users/me/project
  -> run_command(...)
```

### Multi-Turn Editing

```
>>> Read /Users/me/project/config.py
  -> read_file(...)

>>> Add a new field called "debug" with default False
  -> write_file(...)

>>> Now read it back to verify
  -> read_file(...)
```

### Context Management

```
>>> Read a large file...
>>> Do some analysis...
>>> /context
  Est. tokens: ~15000

>>> /clear
Context cleared.

>>> Start fresh task...
```

## Tips

1. **Use absolute paths** - The agent works best with full paths
2. **Clear context between projects** - Use `/clear` when switching tasks
3. **Monitor tokens** - Use `/context` to avoid hitting limits
4. **Multi-turn for complex tasks** - Read first, then ask questions
5. **One-shot for simple tasks** - Use CLI args for quick queries

## Troubleshooting

### "Connection refused"
Ollama isn't running. Run `./start.sh` or `ollama serve`.

### "Model not found"
Pull the model: `ollama pull codestral:22b-v0.1-q8_0`

### Agent stuck in loop
Press Ctrl+C to interrupt, then `/clear` to reset context.

### Context too large
Use `/context` to check, then `/clear` to reset.
