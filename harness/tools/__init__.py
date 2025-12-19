"""Native Python tools for Harness agent."""

from .base import Tool
from .search import SemanticSearchTool

# Registry of all available native tools
NATIVE_TOOLS: dict[str, Tool] = {
    "semantic_search": SemanticSearchTool(),
}

__all__ = ["Tool", "SemanticSearchTool", "NATIVE_TOOLS"]
