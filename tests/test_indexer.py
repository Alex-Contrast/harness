"""Tests for indexer module."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os


class TestChunking(unittest.TestCase):
    """Tests for file chunking logic."""

    def test_chunk_by_lines_splits_correctly(self):
        """_chunk_by_lines should split at line boundaries."""
        from harness.indexer import _chunk_by_lines

        content = "\n".join([f"line {i}" for i in range(250)])
        chunks = _chunk_by_lines(content, max_lines=100)

        self.assertEqual(len(chunks), 3)
        self.assertIn("line 0", chunks[0])
        self.assertIn("line 99", chunks[0])
        self.assertIn("line 100", chunks[1])

    def test_chunk_by_lines_skips_empty(self):
        """_chunk_by_lines should skip empty chunks."""
        from harness.indexer import _chunk_by_lines

        content = "line1\nline2"
        chunks = _chunk_by_lines(content, max_lines=100)

        self.assertEqual(len(chunks), 1)

    def test_chunk_python_file_splits_on_definitions(self):
        """_chunk_python_file should split on class/def boundaries."""
        from harness.indexer import _chunk_python_file

        content = '''import os

def func1():
    pass

def func2():
    pass

class MyClass:
    def method(self):
        pass
'''
        chunks = _chunk_python_file(content)

        # Should have multiple chunks split on definitions
        self.assertGreater(len(chunks), 1)
        # First chunk should have imports
        self.assertIn("import os", chunks[0])

    def test_chunk_file_returns_metadata(self):
        """chunk_file should return chunks with metadata."""
        from harness.indexer import chunk_file

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def hello():\n    print('hello')\n")
            f.flush()
            path = Path(f.name)

        try:
            chunks = chunk_file(path)

            self.assertGreater(len(chunks), 0)
            self.assertEqual(chunks[0]["path"], str(path))
            self.assertEqual(chunks[0]["language"], "py")
            self.assertIn("content", chunks[0])
            self.assertIn("chunk_index", chunks[0])
        finally:
            os.unlink(path)

    def test_chunk_file_handles_missing_file(self):
        """chunk_file should return empty list for missing files."""
        from harness.indexer import chunk_file

        chunks = chunk_file(Path("/nonexistent/file.py"))

        self.assertEqual(chunks, [])


class TestIndexing(unittest.TestCase):
    """Tests for indexing functions."""

    @patch("harness.indexer.get_client")
    @patch("harness.indexer.embed_batch")
    def test_index_file_creates_points(self, mock_embed, mock_get_client):
        """index_file should create Qdrant points."""
        from harness.indexer import index_file

        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_embed.return_value = [[0.1] * 768]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test(): pass\n")
            f.flush()
            path = Path(f.name)

        try:
            count = index_file(path)

            self.assertGreater(count, 0)
            mock_client.upsert.assert_called_once()
            call_args = mock_client.upsert.call_args
            self.assertEqual(call_args.kwargs["collection_name"], "code")
        finally:
            os.unlink(path)

    @patch("harness.indexer.ensure_collection")
    @patch("harness.indexer.index_file")
    def test_index_directory_finds_supported_files(self, mock_index_file, mock_ensure):
        """index_directory should find and index supported files."""
        from harness.indexer import index_directory

        mock_index_file.return_value = 1

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "test.py").write_text("print('hello')")
            (Path(tmpdir) / "test.js").write_text("console.log('hello')")
            (Path(tmpdir) / "test.txt").write_text("ignored")

            count = index_directory(tmpdir, extensions={".py", ".js"})

            # Should have indexed .py and .js but not .txt
            self.assertEqual(mock_index_file.call_count, 2)

    @patch("harness.indexer.ensure_collection")
    @patch("harness.indexer.index_file")
    def test_index_directory_skips_hidden(self, mock_index_file, mock_ensure):
        """index_directory should skip hidden directories."""
        from harness.indexer import index_directory

        mock_index_file.return_value = 1

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create hidden directory with file
            hidden = Path(tmpdir) / ".hidden"
            hidden.mkdir()
            (hidden / "secret.py").write_text("secret")

            # Create normal file
            (Path(tmpdir) / "normal.py").write_text("normal")

            index_directory(tmpdir, extensions={".py"})

            # Should only index normal.py, not .hidden/secret.py
            self.assertEqual(mock_index_file.call_count, 1)


class TestIdGeneration(unittest.TestCase):
    """Tests for ID generation."""

    def test_generate_id_is_deterministic(self):
        """_generate_id should be deterministic for same input."""
        from harness.indexer import _generate_id

        id1 = _generate_id("/path/to/file.py", 0)
        id2 = _generate_id("/path/to/file.py", 0)

        self.assertEqual(id1, id2)

    def test_generate_id_differs_for_different_input(self):
        """_generate_id should differ for different inputs."""
        from harness.indexer import _generate_id

        id1 = _generate_id("/path/to/file.py", 0)
        id2 = _generate_id("/path/to/file.py", 1)
        id3 = _generate_id("/path/to/other.py", 0)

        self.assertNotEqual(id1, id2)
        self.assertNotEqual(id1, id3)


if __name__ == "__main__":
    unittest.main()
