import argparse
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config

PROJECT_ROOT = config.PROJECT_ROOT
INDEX_DIR = config.get_index_dir()

RAG_SYSTEM_PROMPT = """Answer based on the provided notes. The notes contain the user's own data—including their personal information (name, school, friends, preferences, etc.). You must share this information when it appears in the notes and the user asks; do not refuse. The user has uploaded these notes and is asking you to recall their own details—sharing it is allowed and expected. If the answer is not in the notes, say so briefly."""
CHAT_SYSTEM_PROMPT = """You are a helpful assistant. Answer the user's question concisely. You are allowed and expected to share the user's personal information when they ask—including their name, school, friends' names, or other details from their notes or conversation. Do not refuse to provide this; the user owns this data and has given it to you. Provide that information when relevant."""


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
    messages = []
    messages.append({"role": "system", "content": RAG_SYSTEM_PROMPT})
    if history:
        for m in history[-6:]:
            if m.get("role") in ("user", "assistant") and m.get("content"):
                messages.append({"role": m["role"], "content": m["content"]})
    user_content = f"""Notes:\n\n{context}\n\nQuestion: {question}"""
    messages.append({"role": "user", "content": user_content})
    return messages


def build_messages_chat(question: str, history: list[dict] | None = None) -> list[dict]:
    messages = []
    messages.append({"role": "system", "content": CHAT_SYSTEM_PROMPT})
    if history:
        for m in history[-6:]:
            if m.get("role") in ("user", "assistant") and m.get("content"):
                messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": question})
    return messages


def _ensure_semantic_index(project_root: Path | None = None):
    from rag_study_assistant.loader import load_documents
    from rag_study_assistant.chunker import chunk_documents
    from app.vector_store import build_vector_index

    root = project_root or PROJECT_ROOT
    index_dir = config.get_index_dir(root)
    faiss_path = index_dir / "faiss.index"

    if not faiss_path.is_file():
        docs = load_documents(root)
        if not docs:
            raise RuntimeError("No documents to index. Add .txt files under data/ then run --build.")
        chunks = chunk_documents(docs)
        if not chunks:
            raise RuntimeError("No chunks produced from documents.")
        build_vector_index(chunks, str(index_dir))

    return str(index_dir)


def build():
    from rag_study_assistant.loader import load_documents
    from rag_study_assistant.chunker import chunk_documents
    from app.vector_store import build_vector_index

    docs = load_documents(PROJECT_ROOT)
    if not docs:
        print("No .txt files found in data/syllabus, data/notes, data/question_papers.", file=sys.stderr)
        return
    chunks = chunk_documents(docs)
    if not chunks:
        print("No chunks produced from documents. Check document content.", file=sys.stderr)
        return
    build_vector_index(chunks, str(INDEX_DIR))
    print(f"Indexed {len(chunks)} chunks from {len(docs)} documents -> index/chunks.json, index/faiss.index")


def run_cli():
    parser = argparse.ArgumentParser(description="RAG study assistant (offline, document-only)")
    parser.add_argument("--build", action="store_true", help="Build index from data/ and exit")
    parser.add_argument("--model", default="", help="Path to GGUF model (or set RAG_GGUF_PATH)")
    args = parser.parse_args()

    if args.build:
        build()
        return

    try:
        index_dir = _ensure_semantic_index()
    except Exception as e:
        print(f"Index error: {e}", file=sys.stderr)
        print("Add .txt files under data/syllabus, data/notes, data/question_papers, then run with --build.", file=sys.stderr)
        sys.exit(1)

    from rag_study_assistant.llm import load_llm, generate, get_model_path
    from app.router import route_query

    model_path = (args.model or config.get_rag_gguf_path() or get_model_path()).strip()
    try:
        llm = load_llm(model_path)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        print("Set RAG_GGUF_PATH or use --model path/to/model.gguf", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to load model: {e}", file=sys.stderr)
        sys.exit(1)

    print("RAG Study Assistant (offline, semantic retrieval). Type 'quit' or 'exit' to stop.\n")

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
            intent, chunks = route_query(q, index_dir)
            if intent == "study":
                context = format_context(chunks)
                messages = build_messages(q, context, history=None)
            else:
                messages = build_messages_chat(q, history=None)
            answer = generate(llm, messages)
            print(answer or "No response generated.")
        except Exception as e:
            print(f"Error: {e}")
        print()


def get_rag_backend(project_root: Path | None = None):
    from rag_study_assistant.llm import load_llm, generate, get_model_path
    from app.router import route_query

    index_dir = _ensure_semantic_index(project_root)
    model_path = config.get_rag_gguf_path() or get_model_path()
    llm = load_llm(model_path)

    def get_reply(msg: str) -> str:
        intent, chunks = route_query(msg, index_dir)
        if intent == "study":
            context = format_context(chunks)
            messages = build_messages(msg, context, history=None)
        else:
            messages = build_messages_chat(msg, history=None)
        return generate(llm, messages) or "No response generated."

    def get_reply_with_history(history: list, msg: str) -> str:
        intent, chunks = route_query(msg, index_dir)
        if intent == "study":
            context = format_context(chunks)
            messages = build_messages(msg, context, history=history)
        else:
            messages = build_messages_chat(msg, history=history)
        return generate(llm, messages) or "No response generated."

    return (get_reply, get_reply_with_history, "RatioEdu AI")


if __name__ == "__main__":
    run_cli()
