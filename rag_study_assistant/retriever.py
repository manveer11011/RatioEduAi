from rank_bm25 import BM25Okapi

from rag_study_assistant.tokenizer import tokenize_for_bm25


def retrieve(
    query: str,
    chunks: list[dict],
    bm25: BM25Okapi,
    top_k: int = 5,
    prefer_types: tuple[str, ...] = ("method", "example"),
) -> list[dict]:
    if not chunks or not query.strip():
        return []
    tokenized_query = tokenize_for_bm25(query)
    if not tokenized_query:
        return []
    scores = bm25.get_scores(tokenized_query)
    # allow zero scores so we don't drop all results when BM25 is conservative (e.g. short queries)
    if hasattr(scores, "tolist"):
        scores = scores.tolist()
    type_bonus = {t: 1.5 for t in prefer_types}
    for i, c in enumerate(chunks):
        t = (c.get("type") or "").lower()
        if t in type_bonus:
            scores[i] *= type_bonus[t]
    top_n = min(top_k * 2, len(chunks))
    indices = sorted(range(len(scores)), key=lambda i: (-scores[i], -i))[:top_n]
    seen = set()
    result = []
    for i in indices:
        if scores[i] < 0:
            continue
        c = chunks[i]
        key = (c.get("source_file", ""), c.get("type", ""), c.get("text", "")[:80])
        if key in seen:
            continue
        seen.add(key)
        result.append({**c, "score": float(scores[i])})
        if len(result) >= top_k:
            break
    # if nothing matched (all scores 0 or no overlap), still return top chunk so we use index data
    if not result and chunks:
        result = [{**chunks[0], "score": 0.0}]
    return result
