import json
from pathlib import Path

import faiss
import numpy as np

from app.embedder import embed_text


def build_vector_index(chunks, index_dir="index"):
    index_dir = Path(index_dir)
    if not chunks:
        raise ValueError("Cannot build index: no chunks provided.")
    index_dir.mkdir(parents=True, exist_ok=True)

    texts = [c.get("text", "") or "" for c in chunks]
    embeddings = [embed_text(t) for t in texts]

    embeddings = np.array(embeddings).astype("float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    faiss.write_index(index, str(index_dir / "faiss.index"))

    with open(index_dir / "chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=0)
