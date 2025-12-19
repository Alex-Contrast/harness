"""Qdrant client singleton for vector search."""

import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Singleton client instance
_client: QdrantClient | None = None

# Collection configuration
CODE_COLLECTION = "code"
VECTOR_SIZE = 768  # nomic-embed-text dimension


def get_client() -> QdrantClient:
    """Get or create the Qdrant client singleton."""
    global _client
    if _client is None:
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        _client = QdrantClient(host=host, port=port)
    return _client


def ensure_collection() -> None:
    """Ensure the code collection exists with correct configuration."""
    client = get_client()
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if CODE_COLLECTION not in collection_names:
        client.create_collection(
            collection_name=CODE_COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )


def reset_collection() -> None:
    """Delete and recreate the code collection."""
    client = get_client()
    try:
        client.delete_collection(collection_name=CODE_COLLECTION)
    except Exception:
        pass  # Collection may not exist
    ensure_collection()
