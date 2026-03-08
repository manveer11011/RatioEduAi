import re
from app.semantic_retriever import retrieve_semantic

THRESHOLD = 1.2

# Questions about the user's own info should always use RAG (notes may contain personal data)
PERSONAL_INFO_PATTERNS = re.compile(
    r"\b(my\s+name|what(?:'s| is)\s+my\s+name|who\s+am\s+i|tell\s+me\s+my\s+name|"
    r"where\s+do\s+i\s+study|my\s+school|where\s+did\s+i\s+study|"
    r"my\s+info|my\s+personal|about\s+me|my\s+friend|friend'?s?\s+name|"
    r"share\s+personal|personal\s+information)\b",
    re.IGNORECASE,
)


def route_query(query, index_dir="index"):
    q = (query or "").strip()
    chunks, score = retrieve_semantic(q, k=5, index_dir=index_dir)
    # Force study/RAG for personal-info questions so notes are always searched
    if PERSONAL_INFO_PATTERNS.search(q):
        return "study", chunks
    if score < THRESHOLD:
        return "study", chunks
    return "chat", []
