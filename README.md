# RatioEdu

A fully local, CPU-only RAG Study Assistant. Electron desktop app with web UI. No cloud APIs, no GPU required.

---

## Virtual Environment

```
pip install virtualenv
virtualenv env
.\env\Scripts\activate
```

## Git

```
git fetch --all
```

## Folder Structure

```
AI-Teacher/
├── README.md                    # This file
├── requirements.txt             # All dependencies
├── start_backend.py             # Starts RAG backend for Electron
├── run_teacher_web.py           # RAG backend (FastAPI)
├── electron_app/                # Electron desktop UI
│   ├── main.js                  # Launches backend + window
│   └── index.html               # Chat UI (self-contained)
├── rag_study_assistant/         # RAG engine
│   ├── loader.py                # Load .txt from data/
│   ├── chunker.py               # Chunk text (400 tokens, 50 overlap)
│   ├── llm.py                   # Load GGUF via llama-cpp-python
│   └── main.py                  # Build index, get_rag_backend
├── app/                         # Shared modules
│   ├── embedder.py              # Embeddings (GGUF or sentence-transformers)
│   ├── vector_store.py          # FAISS index build
│   ├── semantic_retriever.py    # Semantic search
│   ├── router.py                # Study vs chat routing
│   └── chat_storage.py          # Chat history
├── data/                        # RAG document sources
│   ├── syllabus/
│   ├── notes/
│   └── question_papers/
├── index/                       # FAISS index (built with --build)
│   ├── chunks.json
│   └── faiss.index
└── model/                       # Place GGUF models here
    └── embedding/               # Embedding model (optional)
```

---

## Prerequisites

- Python 3.8+
- GGUF model in `model/` or set `RAG_GGUF_PATH` in `.env`
- Embedding model (optional): set `EMBEDDING_MODEL_PATH` for GGUF or sentence-transformers

---

## How to Run

```bash
pip install -r requirements.txt
cd electron_app && npm install && npm run dev
```

The Electron app will:
1. Build the index if needed (`python -m rag_study_assistant.main --build`)
2. Start the backend (`start_backend.py`)
3. Open the chat UI

**Build index manually:**
```bash
python -m rag_study_assistant.main --build
```

**Web-only (no Electron):**
```bash
python start_backend.py   # or: python run_teacher_web.py
# Open http://127.0.0.1:8000 in browser
```

---

## Configuration (.env)

| Variable | Default | Purpose |
|----------|---------|---------|
| `RAG_GGUF_PATH` | `model/Llama-3.2-1B-Instruct-Q8_0.gguf` | RAG LLM |
| `EMBEDDING_MODEL_PATH` | (sentence-transformers) | Semantic search; use `.gguf` for local embedding |
| `PORT` | 8000 | Backend port |
| `HOST` | 127.0.0.1 | Bind address |

---
