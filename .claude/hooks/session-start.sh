#!/bin/bash
# Claude Code session start hook - loads beads issues for context

set -e

# Get the project directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR"

# Escape function for JSON (macOS compatible)
escape_json() {
    printf '%s' "$1" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'
}

# Gather context
CONTEXT="=== HARNESS PROJECT SESSION ===

"

# Current branch
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
CONTEXT+="Branch: $BRANCH

"

# Open beads issues
if command -v bd &> /dev/null; then
    ISSUES=$(bd list --status open 2>/dev/null || echo "No issues found")
    CONTEXT+="=== OPEN ISSUES ===
$ISSUES

"

    # In-progress issues (priority)
    IN_PROGRESS=$(bd list --status in_progress 2>/dev/null || echo "")
    if [ -n "$IN_PROGRESS" ]; then
        CONTEXT+="=== IN PROGRESS (resume these) ===
$IN_PROGRESS

"
    fi

    # Qdrant issues specifically
    QDRANT=$(bd list --label qdrant 2>/dev/null || echo "")
    if [ -n "$QDRANT" ]; then
        CONTEXT+="=== QDRANT INTEGRATION TASKS ===
$QDRANT

"
    fi
else
    CONTEXT+="WARNING: bd command not found. Install beads: https://github.com/steveyegge/beads

"
fi

# Recent commits
RECENT=$(git log -3 --oneline 2>/dev/null || echo "No commits")
CONTEXT+="=== RECENT COMMITS ===
$RECENT

"

CONTEXT+="=== WORKFLOW REMINDER ===
1. Claim work: bd update <id> --status in_progress
2. View details: bd show <id>
3. End session: bd sync && git push
"

# Get escaped context (strips outer quotes from json.dumps)
ESCAPED=$(escape_json "$CONTEXT")

# Output JSON
cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": $ESCAPED
  }
}
EOF
