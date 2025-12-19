"""Semantic search tool using Qdrant."""

from .base import Tool
from ..embedding import embed
from ..qdrant import get_client, CODE_COLLECTION


class SemanticSearchTool(Tool):
    """Search codebase for relevant code using natural language."""

    name = "semantic_search"
    description = "Search codebase for relevant code using natural language query"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)"
                }
            },
            "required": ["query"]
        }

    def execute(self, query: str, limit: int = 5) -> str:
        """Execute semantic search and return formatted results.

        Args:
            query: Natural language search query.
            limit: Maximum number of results to return.

        Returns:
            Formatted search results with code snippets.
        """
        try:
            # Embed the query
            query_embedding = embed(query)

            # Search Qdrant
            client = get_client()
            results = client.query_points(
                collection_name=CODE_COLLECTION,
                query=query_embedding,
                limit=limit
            )

            if not results.points:
                return "No results found."

            # Format results
            output = []
            for r in results.points:
                path = r.payload.get("path", "unknown")
                language = r.payload.get("language", "")
                content = r.payload.get("content", "")
                score = r.score

                # Truncate long content
                if len(content) > 1000:
                    content = content[:1000] + "\n... (truncated)"

                output.append(
                    f"## {path} (score: {score:.3f})\n"
                    f"```{language}\n{content}\n```"
                )

            return "\n\n".join(output)

        except Exception as e:
            return f"Search error: {e}"
