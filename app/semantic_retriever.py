import faiss
import json
import numpy as np
from pathlib import Path

from app.embedder import embed_text

_index_cache = {}
_chunks_cache = {}


def _load_index(index_dir: str | Path):
    index_dir = Path(index_dir)
    key = str(index_dir.resolve())
    if key not in _index_cache:
        index_path = index_dir / "faiss.index"
        chunks_path = index_dir / "chunks.json"
        if not index_path.is_file() or not chunks_path.is_file():
            raise FileNotFoundError(
                f"FAISS index not found at {index_dir}. Run with --build to create index."
            )
        _index_cache[key] = faiss.read_index(str(index_path))
        with open(chunks_path, "r", encoding="utf-8") as f:
            _chunks_cache[key] = json.load(f)
    return _index_cache[key], _chunks_cache[key]


def retrieve_semantic(query, k=5, index_dir="index"):
    if query is None:
        query = ""
    index, chunks = _load_index(index_dir)
    if not chunks:
        return [], float("inf")
    q_embed = embed_text(query).astype("float32").reshape(1, -1)
    distances, indices = index.search(q_embed, k)

    results = [chunks[i] for i in indices[0] if 0 <= i < len(chunks)]
    best_score = float(distances[0][0]) if distances.size else float("inf")

    return results, best_score
