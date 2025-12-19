"""Tests for Qdrant client module."""

import unittest
from unittest.mock import Mock, patch, MagicMock


class TestQdrantClient(unittest.TestCase):
    """Tests for qdrant.py module."""

    def setUp(self):
        # Reset singleton between tests
        import harness.qdrant as qdrant_module
        qdrant_module._client = None

    @patch("harness.qdrant.QdrantClient")
    def test_get_client_creates_singleton(self, mock_qdrant_class):
        """get_client should create a singleton QdrantClient."""
        from harness.qdrant import get_client

        mock_instance = Mock()
        mock_qdrant_class.return_value = mock_instance

        client1 = get_client()
        client2 = get_client()

        # Should only create one instance
        mock_qdrant_class.assert_called_once_with(host="localhost", port=6333)
        self.assertIs(client1, client2)

    @patch.dict("os.environ", {"QDRANT_HOST": "qdrant.local", "QDRANT_PORT": "6334"})
    @patch("harness.qdrant.QdrantClient")
    def test_get_client_reads_env_vars(self, mock_qdrant_class):
        """get_client should read host/port from environment."""
        from harness.qdrant import get_client

        get_client()

        mock_qdrant_class.assert_called_once_with(host="qdrant.local", port=6334)

    @patch("harness.qdrant.get_client")
    def test_ensure_collection_creates_if_missing(self, mock_get_client):
        """ensure_collection should create collection if it doesn't exist."""
        from harness.qdrant import ensure_collection, CODE_COLLECTION, VECTOR_SIZE

        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Simulate empty collections list
        mock_client.get_collections.return_value.collections = []

        ensure_collection()

        mock_client.create_collection.assert_called_once()
        call_args = mock_client.create_collection.call_args
        self.assertEqual(call_args.kwargs["collection_name"], CODE_COLLECTION)

    @patch("harness.qdrant.get_client")
    def test_ensure_collection_skips_if_exists(self, mock_get_client):
        """ensure_collection should not create if collection exists."""
        from harness.qdrant import ensure_collection, CODE_COLLECTION

        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Simulate collection already exists
        mock_collection = Mock()
        mock_collection.name = CODE_COLLECTION
        mock_client.get_collections.return_value.collections = [mock_collection]

        ensure_collection()

        mock_client.create_collection.assert_not_called()

    @patch("harness.qdrant.get_client")
    def test_reset_collection_deletes_and_recreates(self, mock_get_client):
        """reset_collection should delete then recreate."""
        from harness.qdrant import reset_collection, CODE_COLLECTION

        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.get_collections.return_value.collections = []

        reset_collection()

        mock_client.delete_collection.assert_called_once_with(
            collection_name=CODE_COLLECTION
        )
        mock_client.create_collection.assert_called_once()


class TestQdrantConstants(unittest.TestCase):
    """Tests for module constants."""

    def test_vector_size_matches_nomic_embed(self):
        """VECTOR_SIZE should be 768 for nomic-embed-text."""
        from harness.qdrant import VECTOR_SIZE

        self.assertEqual(VECTOR_SIZE, 768)

    def test_collection_name(self):
        """CODE_COLLECTION should be 'code'."""
        from harness.qdrant import CODE_COLLECTION

        self.assertEqual(CODE_COLLECTION, "code")


if __name__ == "__main__":
    unittest.main()
