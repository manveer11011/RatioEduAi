import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = PROJECT_ROOT / "index"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# RAG: format retrieved chunks and build chat messages
RAG_SYSTEM_PROMPT = "Answer based only on the provided notes. If the answer is not in the notes, say so briefly."


def format_context(chunks: list[dict]) -> str:
    if not chunks:
        return "(No relevant notes provided.)"
    parts = []
    for i, c in enumerate(chunks, 1):
        text = (c.get("text") or "").strip()
        if not text:
            continue
        source = c.get("source_file", "unknown")
        ctype = c.get("type", "theory")
        parts.append(f"[{i}] (source: {source}, type: {ctype})\n{text}")
    return "\n\n---\n\n".join(parts) if parts else "(No relevant notes provided.)"


def build_messages(question: str, context: str, history: list[dict] | None = None) -> list[dict]:
    """Build chat messages: optional system, optional history (last 6 messages), then current question with context."""
    messages = []
    messages.append({"role": "system", "content": RAG_SYSTEM_PROMPT})
    if history:
        # Keep last 6 messages (3 turns) to stay within context window
        for m in history[-6:]:
            if m.get("role") in ("user", "assistant") and m.get("content"):
                messages.append({"role": m["role"], "content": m["content"]})
    user_content = f"""Notes:\n\n{context}\n\nQuestion: {question}"""
    messages.append({"role": "user", "content": user_content})
    return messages


def _ensure_index(project_root: Path | None = None):
    from rag_study_assistant.indexer import load_index, build_index
    from rag_study_assistant.loader import load_documents
    from rag_study_assistant.chunker import chunk_documents

    root = project_root or PROJECT_ROOT
    index_dir = root / "index"
    chunks, bm25 = load_index(index_dir)
    if not chunks:
        docs = load_documents(root)
        if not docs:
            return [], bm25
        chunks = chunk_documents(docs)
        if not chunks:
            return [], bm25
        build_index(chunks, index_dir)
        chunks, bm25 = load_index(index_dir)
    return chunks, bm25


def build():
    from rag_study_assistant.loader import load_documents
    from rag_study_assistant.chunker import chunk_documents
    from rag_study_assistant.indexer import build_index

    docs = load_documents(PROJECT_ROOT)
    if not docs:
        print("No .txt files found in data/syllabus, data/notes, data/question_papers.", file=sys.stderr)
        return
    chunks = chunk_documents(docs)
    build_index(chunks, INDEX_DIR)
    print(f"Indexed {len(chunks)} chunks from {len(docs)} documents -> index/documents.json")


def run_cli():
    parser = argparse.ArgumentParser(description="RAG study assistant (offline, document-only)")
    parser.add_argument("--build", action="store_true", help="Build index from data/ and exit")
    parser.add_argument("--model", default="", help="Path to GGUF model (or set RAG_GGUF_PATH)")
    args = parser.parse_args()

    if args.build:
        build()
        return

    try:
        chunks, bm25 = _ensure_index()
    except Exception as e:
        print(f"Index error: {e}", file=sys.stderr)
        chunks, bm25 = [], None

    if not chunks or bm25 is None:
        print("No documents in index. Add .txt files under data/syllabus, data/notes, data/question_papers, then run with --build.", file=sys.stderr)
        sys.exit(1)

    from rag_study_assistant.llm import load_llm, generate, get_model_path
    model_path = (args.model or os.environ.get("RAG_GGUF_PATH", "") or get_model_path()).strip()
    try:
        llm = load_llm(model_path)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        print("Set RAG_GGUF_PATH or use --model path/to/model.gguf", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to load model: {e}", file=sys.stderr)
        sys.exit(1)

    from rag_study_assistant.retriever import retrieve

    print("RAG Study Assistant (offline, document-only). Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            q = input("Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if not q:
            continue
        if q.lower() in ("quit", "exit", "q"):
            print("Bye.")
            break

        try:
            top = retrieve(q, chunks, bm25, top_k=5)
            context = format_context(top)
            messages = build_messages(q, context, history=None)
            answer = generate(llm, messages)
            print(answer or "No response generated.")
        except Exception as e:
            print(f"Error: {e}")
        print()


def get_rag_backend(project_root: Path | None = None):
    """Return (get_reply, get_reply_with_history, backend_name) for web API.
    Pass project_root to force index path (e.g. Path(__file__).resolve().parent when running from web).
    """
    from rag_study_assistant.llm import load_llm, generate, get_model_path
    from rag_study_assistant.retriever import retrieve

    chunks, bm25 = _ensure_index(project_root)
    if not chunks or bm25 is None:
        raise RuntimeError(
            "No documents in index. Add .txt files under data/syllabus, data/notes, data/question_papers, then run: python -m rag_study_assistant.main --build"
        )
    model_path = os.environ.get("RAG_GGUF_PATH", "").strip() or get_model_path()
    llm = load_llm(model_path)

    def get_reply(msg: str) -> str:
        top = retrieve(msg, chunks, bm25, top_k=5)
        context = format_context(top)
        messages = build_messages(msg, context, history=None)
        return generate(llm, messages) or "No response generated."

    def get_reply_with_history(history: list, msg: str) -> str:
        top = retrieve(msg, chunks, bm25, top_k=5)
        context = format_context(top)
        messages = build_messages(msg, context, history=history)
        return generate(llm, messages) or "No response generated."

    return (get_reply, get_reply_with_history, "RAG")


if __name__ == "__main__":
    run_cli()
