"""Tests for embedding module."""

import unittest
from unittest.mock import Mock, patch


class TestEmbedding(unittest.TestCase):
    """Tests for embedding.py module."""

    def setUp(self):
        # Reset singleton between tests
        import harness.embedding as embed_module
        embed_module._ollama_client = None

    @patch("harness.embedding.Client")
    def test_embed_returns_vector(self, mock_client_class):
        """embed should return a 768-dim vector."""
        from harness.embedding import embed

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock embedding response
        fake_embedding = [0.1] * 768
        mock_client.embed.return_value = {"embeddings": [fake_embedding]}

        result = embed("test text")

        self.assertEqual(result, fake_embedding)
        mock_client.embed.assert_called_once_with(
            model="nomic-embed-text", input="test text"
        )

    @patch("harness.embedding.Client")
    def test_embed_batch_returns_multiple_vectors(self, mock_client_class):
        """embed_batch should return list of vectors."""
        from harness.embedding import embed_batch

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock batch embedding response
        fake_embeddings = [[0.1] * 768, [0.2] * 768, [0.3] * 768]
        mock_client.embed.return_value = {"embeddings": fake_embeddings}

        texts = ["text1", "text2", "text3"]
        result = embed_batch(texts)

        self.assertEqual(result, fake_embeddings)
        mock_client.embed.assert_called_once_with(
            model="nomic-embed-text", input=texts
        )

    @patch.dict("os.environ", {"OLLAMA_HOST": "http://ollama.local:11434"})
    @patch("harness.embedding.Client")
    def test_client_reads_env_var(self, mock_client_class):
        """Client should use OLLAMA_HOST from environment."""
        from harness.embedding import embed

        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.embed.return_value = {"embeddings": [[0.1] * 768]}

        embed("test")

        mock_client_class.assert_called_once_with(host="http://ollama.local:11434")


class TestEmbeddingConstants(unittest.TestCase):
    """Tests for module constants."""

    def test_embed_model(self):
        """EMBED_MODEL should be nomic-embed-text."""
        from harness.embedding import EMBED_MODEL

        self.assertEqual(EMBED_MODEL, "nomic-embed-text")


if __name__ == "__main__":
    unittest.main()
