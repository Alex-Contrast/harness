"""Code indexer for Qdrant with chunking strategy."""

import hashlib
from pathlib import Path
from qdrant_client.models import PointStruct

from .embedding import embed_batch
from .qdrant import get_client, ensure_collection, CODE_COLLECTION

# Supported file extensions
SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".go", ".rs", ".java", ".md"}

# Chunking configuration
MAX_CHUNK_LINES = 100
MAX_CHUNK_CHARS = 4000


def _generate_id(path: str, chunk_index: int) -> int:
    """Generate a stable ID for a chunk."""
    key = f"{path}:{chunk_index}"
    return int(hashlib.md5(key.encode()).hexdigest()[:16], 16)


def _chunk_by_lines(content: str, max_lines: int = MAX_CHUNK_LINES) -> list[str]:
    """Split content into chunks by line count."""
    lines = content.split("\n")
    chunks = []

    for i in range(0, len(lines), max_lines):
        chunk = "\n".join(lines[i:i + max_lines])
        if chunk.strip():  # Skip empty chunks
            chunks.append(chunk)

    return chunks


def _chunk_python_file(content: str) -> list[str]:
    """Chunk Python file by function/class boundaries when possible."""
    import re

    # Try to split by top-level definitions
    pattern = r'^(class |def |async def )'
    lines = content.split("\n")

    chunks = []
    current_chunk_lines = []

    for line in lines:
        # Start new chunk at class/function definition
        if re.match(pattern, line) and current_chunk_lines:
            chunk = "\n".join(current_chunk_lines)
            if chunk.strip():
                chunks.append(chunk)
            current_chunk_lines = []

        current_chunk_lines.append(line)

        # Also split if chunk gets too large
        if len(current_chunk_lines) >= MAX_CHUNK_LINES:
            chunk = "\n".join(current_chunk_lines)
            if chunk.strip():
                chunks.append(chunk)
            current_chunk_lines = []

    # Don't forget the last chunk
    if current_chunk_lines:
        chunk = "\n".join(current_chunk_lines)
        if chunk.strip():
            chunks.append(chunk)

    return chunks if chunks else [content]


def chunk_file(path: Path) -> list[dict]:
    """Split file into chunks with metadata.

    Args:
        path: Path to the file.

    Returns:
        List of chunk dictionaries with content, path, and language.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return []

    # Skip very large files
    if len(content) > 100000:
        content = content[:100000]

    # Choose chunking strategy based on file type
    suffix = path.suffix.lower()
    if suffix == ".py":
        chunks = _chunk_python_file(content)
    else:
        chunks = _chunk_by_lines(content)

    # Truncate individual chunks if too long
    results = []
    for i, chunk in enumerate(chunks):
        if len(chunk) > MAX_CHUNK_CHARS:
            chunk = chunk[:MAX_CHUNK_CHARS]

        results.append({
            "content": chunk,
            "path": str(path),
            "language": suffix.lstrip(".") or "text",
            "chunk_index": i
        })

    return results


def index_file(path: Path) -> int:
    """Index a single file into Qdrant.

    Args:
        path: Path to the file.

    Returns:
        Number of chunks indexed.
    """
    chunks = chunk_file(path)
    if not chunks:
        return 0

    # Generate embeddings for all chunks at once
    texts = [c["content"] for c in chunks]
    embeddings = embed_batch(texts)

    # Create points
    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        points.append(PointStruct(
            id=_generate_id(chunk["path"], chunk["chunk_index"]),
            vector=embedding,
            payload=chunk
        ))

    # Upsert to Qdrant
    client = get_client()
    client.upsert(collection_name=CODE_COLLECTION, points=points)

    return len(points)


def index_directory(directory: str, extensions: set[str] | None = None) -> int:
    """Index all supported files in a directory.

    Args:
        directory: Path to directory to index.
        extensions: Set of file extensions to index (e.g., {".py", ".js"}).
                   Defaults to SUPPORTED_EXTENSIONS.

    Returns:
        Total number of chunks indexed.
    """
    if extensions is None:
        extensions = SUPPORTED_EXTENSIONS

    ensure_collection()

    root = Path(directory)
    total_chunks = 0

    for ext in extensions:
        for path in root.rglob(f"*{ext}"):
            # Skip hidden directories and common ignore patterns
            parts = path.parts
            if any(p.startswith(".") or p in {"node_modules", "__pycache__", "venv", ".venv"}
                   for p in parts):
                continue

            try:
                chunks = index_file(path)
                if chunks:
                    print(f"  Indexed {path}: {chunks} chunks")
                    total_chunks += chunks
            except Exception as e:
                print(f"  Error indexing {path}: {e}")

    return total_chunks
