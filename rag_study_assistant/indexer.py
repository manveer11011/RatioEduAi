import json
from pathlib import Path

from rank_bm25 import BM25Okapi

from rag_study_assistant.tokenizer import tokenize_for_bm25


def build_index(chunks: list[dict], index_dir: str | Path) -> None:
    index_path = Path(index_dir) / "documents.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [{"text": c.get("text", ""), "source_file": c.get("source_file", ""),
                "subject": c.get("subject", ""), "chapter": c.get("chapter", ""),
                "type": c.get("type", "theory")} for c in chunks]
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=0)


def load_index(index_dir: str | Path) -> tuple[list[dict], BM25Okapi]:
    index_path = Path(index_dir) / "documents.json"
    if not index_path.is_file():
        return [], BM25Okapi([[]])
    with open(index_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    if not chunks:
        return [], BM25Okapi([[]])
    tokenized = [tokenize_for_bm25(c.get("text", "")) for c in chunks]
    bm25 = BM25Okapi(tokenized)
    return chunks, bm25
