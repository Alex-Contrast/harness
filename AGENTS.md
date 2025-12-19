# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Project Status

**Harness** is a local-first AI coding agent built with Python, Ollama, and Qdrant.

### Completed
- Phase 1: Python Agent Core (basic agent loop with MCP)
- Phase 3: K8s production patterns (probes, PDBs)
- Phase 4: Job-based agent architecture
- Phase 6: Helm chart packaging

### In Progress
- **Phase 2: Qdrant Integration** - Vector search for semantic code retrieval
- **Phase 5: Automation** - CronJobs and workflow automation

### Key Files
| File | Purpose |
|------|---------|
| `plan.md` | Overall project architecture and Phase 1-3 details |
| `k8s_plan.md` | K8s deployment strategy and Phase 4-6 details |
| `harness/agent.py` | Main agent loop implementation |
| `harness/config.py` | Configuration management |
| `.beads/issues.jsonl` | Issue tracking data (synced with git) |

---

## Session Workflow

### Starting a Session

```bash
# 1. Get latest changes
git pull --rebase

# 2. Import any updated issues
bd sync

# 3. See what's available
bd ready              # Find issues ready for work
bd list --label qdrant   # Filter by label
bd list --status open    # Filter by status
```

### Working on Issues

```bash
# 1. Claim an issue
bd update <id> --status in_progress

# 2. View issue details
bd show <id>

# 3. Work on the issue...

# 4. Add notes as you work
bd comment <id> "Started implementing embedding pipeline"
```

### Ending a Session (MANDATORY)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git add -A && git commit -m "session progress"
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Verify** - All changes committed AND pushed

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

---

## Quick Reference

```bash
# Issue Management
bd create "Title" --description "Details" --label phase2
bd list                    # All issues
bd list --status open      # Open issues only
bd list --label qdrant     # Filter by label
bd ready                   # Issues ready for work
bd show <id>               # View details
bd update <id> --status in_progress  # Claim work
bd update <id> --status done         # Mark done
bd close <id>              # Close issue
bd comment <id> "Note"     # Add comment

# Git Sync
bd sync                    # Export to JSONL and sync with git

# Filtering
bd list --label phase2     # By label
bd list --priority P1      # By priority
bd list --type bug         # By type
```

---

## Current Open Issues

Run `bd list` to see current issues. Key areas:

### Qdrant Integration (Phase 2)
- `harness-b8w`: Set up qdrant-client singleton
- `harness-mpy`: Embedding pipeline with nomic-embed-text
- `harness-v8y`: Code indexer with chunking strategy
- `harness-xzs`: SemanticSearchTool for agent

### Automation (Phase 5)
- `harness-ote`: CronJob for scheduled reindexing
- `harness-ci3`: On-demand indexing Job
- `harness-3r8`: Git webhook trigger (optional)

### Other
- `harness-06u`: Test parallel job execution

---

## Architecture Reference

```
harness/
├── harness/           # Python agent code
│   ├── agent.py       # Agent loop (MCP-based)
│   ├── config.py      # Configuration
│   └── mcp_client.py  # MCP tool integration
├── k8s/               # Raw K8s manifests
├── harness-chart/     # Helm chart
├── .beads/            # Issue tracking
│   ├── issues.jsonl   # Issue data (tracked in git)
│   ├── beads.db       # Local SQLite (gitignored)
│   └── config.yaml    # Beads configuration
├── plan.md            # Project plan
└── k8s_plan.md        # K8s deployment plan
```

