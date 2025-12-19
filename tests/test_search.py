"""Tests for semantic search tool."""

import unittest
from unittest.mock import Mock, patch, MagicMock


class TestSemanticSearchTool(unittest.TestCase):
    """Tests for SemanticSearchTool."""

    def test_tool_has_required_attributes(self):
        """Tool should have name, description, parameters."""
        from harness.tools.search import SemanticSearchTool

        tool = SemanticSearchTool()

        self.assertEqual(tool.name, "semantic_search")
        self.assertIn("search", tool.description.lower())
        self.assertIn("query", tool.parameters["properties"])

    def test_parameters_schema(self):
        """Parameters should define query as required string."""
        from harness.tools.search import SemanticSearchTool

        tool = SemanticSearchTool()
        params = tool.parameters

        self.assertEqual(params["type"], "object")
        self.assertIn("query", params["properties"])
        self.assertEqual(params["properties"]["query"]["type"], "string")
        self.assertIn("query", params["required"])

    @patch("harness.tools.search.get_client")
    @patch("harness.tools.search.embed")
    def test_execute_returns_formatted_results(self, mock_embed, mock_get_client):
        """execute should return formatted search results."""
        from harness.tools.search import SemanticSearchTool

        mock_embed.return_value = [0.1] * 768

        # Mock search results
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_point = Mock()
        mock_point.payload = {
            "path": "/test/file.py",
            "language": "py",
            "content": "def hello(): pass"
        }
        mock_point.score = 0.95

        mock_results = Mock()
        mock_results.points = [mock_point]
        mock_client.query_points.return_value = mock_results

        tool = SemanticSearchTool()
        result = tool.execute(query="hello function")

        self.assertIn("/test/file.py", result)
        self.assertIn("0.95", result)
        self.assertIn("def hello", result)

    @patch("harness.tools.search.get_client")
    @patch("harness.tools.search.embed")
    def test_execute_handles_no_results(self, mock_embed, mock_get_client):
        """execute should handle empty results gracefully."""
        from harness.tools.search import SemanticSearchTool

        mock_embed.return_value = [0.1] * 768

        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_results = Mock()
        mock_results.points = []
        mock_client.query_points.return_value = mock_results

        tool = SemanticSearchTool()
        result = tool.execute(query="nonexistent")

        self.assertIn("No results", result)

    @patch("harness.tools.search.get_client")
    @patch("harness.tools.search.embed")
    def test_execute_handles_errors(self, mock_embed, mock_get_client):
        """execute should catch and report errors."""
        from harness.tools.search import SemanticSearchTool

        mock_embed.side_effect = Exception("Connection failed")

        tool = SemanticSearchTool()
        result = tool.execute(query="test")

        self.assertIn("error", result.lower())

    @patch("harness.tools.search.get_client")
    @patch("harness.tools.search.embed")
    def test_execute_respects_limit(self, mock_embed, mock_get_client):
        """execute should pass limit to query."""
        from harness.tools.search import SemanticSearchTool

        mock_embed.return_value = [0.1] * 768

        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_results = Mock()
        mock_results.points = []
        mock_client.query_points.return_value = mock_results

        tool = SemanticSearchTool()
        tool.execute(query="test", limit=10)

        mock_client.query_points.assert_called_once()
        call_kwargs = mock_client.query_points.call_args.kwargs
        self.assertEqual(call_kwargs["limit"], 10)

    @patch("harness.tools.search.get_client")
    @patch("harness.tools.search.embed")
    def test_execute_truncates_long_content(self, mock_embed, mock_get_client):
        """execute should truncate very long content."""
        from harness.tools.search import SemanticSearchTool

        mock_embed.return_value = [0.1] * 768

        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_point = Mock()
        mock_point.payload = {
            "path": "/test/file.py",
            "language": "py",
            "content": "x" * 2000  # Very long content
        }
        mock_point.score = 0.9

        mock_results = Mock()
        mock_results.points = [mock_point]
        mock_client.query_points.return_value = mock_results

        tool = SemanticSearchTool()
        result = tool.execute(query="test")

        self.assertIn("truncated", result)


class TestToolDocumentation(unittest.TestCase):
    """Tests for tool documentation."""

    def test_to_doc_format(self):
        """to_doc should return properly formatted string."""
        from harness.tools.search import SemanticSearchTool

        tool = SemanticSearchTool()
        doc = tool.to_doc()

        self.assertIn("semantic_search", doc)
        self.assertIn("query", doc)
        self.assertTrue(doc.startswith("- "))


class TestNativeToolsRegistry(unittest.TestCase):
    """Tests for native tools registry."""

    def test_semantic_search_in_registry(self):
        """NATIVE_TOOLS should include semantic_search."""
        from harness.tools import NATIVE_TOOLS

        self.assertIn("semantic_search", NATIVE_TOOLS)

    def test_registry_tools_are_instances(self):
        """Registry should contain tool instances, not classes."""
        from harness.tools import NATIVE_TOOLS
        from harness.tools.base import Tool

        for name, tool in NATIVE_TOOLS.items():
            self.assertIsInstance(tool, Tool)


if __name__ == "__main__":
    unittest.main()
