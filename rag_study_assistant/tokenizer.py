"""Shared tokenizer for BM25 indexing and retrieval."""
import re


def tokenize_for_bm25(text: str) -> list[str]:
    """Tokenize text for BM25Okapi (lowercase word tokens)."""
    return re.findall(r"\w+", (text or "").lower())
