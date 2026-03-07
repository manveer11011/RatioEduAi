import re

CHARS_PER_TOKEN = 4
CHUNK_SIZE_TOKENS = 400
OVERLAP_TOKENS = 50
CHUNK_SIZE_CHARS = CHUNK_SIZE_TOKENS * CHARS_PER_TOKEN
OVERLAP_CHARS = OVERLAP_TOKENS * CHARS_PER_TOKEN


def _simple_tokenize(text: str) -> list[str]:
    return re.findall(r"\S+\s*", text) if text else []


def _chars_to_fill_token_approx(char_count: int) -> int:
    return max(0, (char_count + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN)


def chunk_document(doc: dict) -> list[dict]:
    content = (doc.get("content") or "").strip()
    if not content:
        return []
    meta = {
        "source_file": doc.get("source_file", ""),
        "subject": doc.get("subject", "unknown"),
        "chapter": doc.get("chapter", "unknown"),
        "type": doc.get("type", "theory"),
    }
    chunks = []
    start = 0
    while start < len(content):
        end = min(start + CHUNK_SIZE_CHARS, len(content))
        if end < len(content):
            for sep in ("\n\n", "\n", ". ", " "):
                idx = content.rfind(sep, start, end + 1)
                if idx > start:
                    end = idx + len(sep)
                    break
        text = content[start:end].strip()
        if text:
            chunks.append({
                "text": text,
                **meta,
            })
        start = end - OVERLAP_CHARS
        if start < 0 or start >= len(content):
            break
        if start >= end:
            start = end
        if end >= len(content):
            break
    return chunks


def chunk_documents(documents: list[dict]) -> list[dict]:
    out = []
    for doc in documents:
        out.extend(chunk_document(doc))
    return out
