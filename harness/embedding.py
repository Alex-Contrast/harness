"""Embedding generation using Ollama nomic-embed-text."""

import os
from ollama import Client

# Initialize Ollama client
_ollama_client: Client | None = None

# Model configuration
EMBED_MODEL = "nomic-embed-text"


def _get_client() -> Client:
    """Get or create the Ollama client."""
    global _ollama_client
    if _ollama_client is None:
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        _ollama_client = Client(host=host)
    return _ollama_client


def embed(text: str) -> list[float]:
    """Generate embedding for a single text string.

    Args:
        text: The text to embed.

    Returns:
        768-dimensional embedding vector.
    """
    client = _get_client()
    response = client.embed(model=EMBED_MODEL, input=text)
    return response["embeddings"][0]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts.

    Args:
        texts: List of texts to embed.

    Returns:
        List of 768-dimensional embedding vectors.
    """
    client = _get_client()
    response = client.embed(model=EMBED_MODEL, input=texts)
    return response["embeddings"]
