# Local AI Study & Coding Project

A fully local, CPU-only project with two main components: a **Study & Coding Teacher** chatbot and a **RAG Study Assistant** that answers only from your documents. No cloud APIs, no GPU required.

---

## Project Overview

| Component | Purpose |
|-----------|---------|
| **Study & Coding Teacher** | Chatbot that helps with study and coding topics only; refuses off-topic requests |
| **RAG Study Assistant** | Answers questions strictly from your notes; says "Method not found" when the answer isn't in the documents |

Both run on CPU using GGUF models via `llama-cpp-python`.

---

##  Create a Virtual Env 
```
pip install virtualenv 
virtualenv env
.\env\Scripts\activate
```

##  Use this to get the latest branches
```
git fetch --all
```

## Folder Structure

```
lmstudio-community/
├── README.md                    # This file
├── requirements.txt             # All dependencies
│
├── run_teacher_agent.py         # Teacher CLI (interactive chat)
├── run_teacher_ui.py            # Teacher Tkinter desktop UI
├── run_teacher_web.py           # Teacher web server (FastAPI)
│
├── study_coding_teacher_agent/  # Study & Coding Teacher
│   ├── agent.py                 # Teacher logic (OpenAI-compatible interface)
│   ├── gguf_backend.py          # GGUF inference via llama-cpp-python
│   └── backend_runner.py        # Shared backend for UI and web
│
├── rag_study_assistant/         # RAG Study Assistant
│   ├── loader.py                # Load .txt from data/
│   ├── chunker.py               # Chunk text (400 tokens, 50 overlap)
│   ├── indexer.py               # BM25 index, stores index/documents.json
│   ├── retriever.py             # Fetch top 5 chunks (prefer method/example)
│   ├── llm.py                   # Load GGUF, 2048 ctx, temp 0.2
│   └── main.py                  # CLI: build index or Q&A loop
│
├── web_ui/                      # Teacher web frontend
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── data/                        # RAG document sources
│   ├── syllabus/                # Syllabus .txt files
│   ├── notes/                   # Notes .txt files (theory, method, example)
│   └── question_papers/         # Question .txt files
│
├── index/                       # RAG index output
│   └── documents.json           # Built by rag_study_assistant (--build)
│
└── gpt-oss-20b-GGUF/           # Place your GGUF model here
    └── gpt-oss-20b-MXFP4.gguf
```

---

## Prerequisites

- **Python 3.8+**
- **GGUF model**: Place an instruct GGUF model at `gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf`  
  Or set: `GGUF_PATH` (Teacher) or `RAG_GGUF_PATH` (RAG) to your model path.

---

## How to Run Locally

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Place Your GGUF Model

Put your model at `gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf` or:

```bash
set GGUF_PATH=C:\path\to\your\model.gguf      # Teacher
set RAG_GGUF_PATH=C:\path\to\your\model.gguf  # RAG
```

### 3. Run Study & Coding Teacher

```bash
python run_teacher_agent.py   # CLI
python run_teacher_ui.py      # Tkinter UI
python run_teacher_web.py     # Web UI → http://localhost:8765
```

### 4. Run RAG Study Assistant

**Add documents** to `data/syllabus/`, `data/notes/`, `data/question_papers/`  
Use filenames like `method_algebra.txt`, `example_calc.txt` for type hints.

**Build index:**
```bash
python -m rag_study_assistant.main --build
```

**Ask questions:**
```bash
python -m rag_study_assistant.main
```

---

## How to Implement Locally for Others

### Use the Teacher in Your Code

```python
from llama_cpp import Llama
from study_coding_teacher_agent.gguf_backend import get_teacher_response_gguf

llm = Llama(model_path="path/to/model.gguf", n_ctx=8192, n_gpu_layers=0)
reply = get_teacher_response_gguf(llm, "Explain recursion in Python")
print(reply)
```

Options: `use_short_prompt=True`, `use_guard=False`

### Use the RAG Assistant in Your Code

```python
from rag_study_assistant.loader import load_documents
from rag_study_assistant.chunker import chunk_documents
from rag_study_assistant.indexer import load_index, build_index
from rag_study_assistant.retriever import retrieve
from rag_study_assistant.main import format_context, build_messages
from rag_study_assistant.llm import load_llm, generate

chunks, bm25 = load_index("index/")
top = retrieve("Your question", chunks, bm25, top_k=5)
context = format_context(top)
messages = build_messages("Your question", context)
llm = load_llm()
answer = generate(llm, messages)
```

### Distributing to Others

1. Include `requirements.txt`
2. Instruct users to place a GGUF model in `gpt-oss-20b-GGUF/` or set `GGUF_PATH`
3. For RAG: add `.txt` files to `data/` and run `python -m rag_study_assistant.main --build`
4. Web UI: `pip install -r requirements.txt` then `python run_teacher_web.py`

---

## Configuration

| Variable | Default | Used By |
|----------|---------|---------|
| `GGUF_PATH` | `gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf` | Teacher |
| `RAG_GGUF_PATH` | Same | RAG |
| `PORT` | 8765 | Web UI |
| `HOST` | 127.0.0.1 | Web UI |

---

## Model Settings

- **Teacher**: n_ctx=8192, n_gpu_layers=0 (CPU)
- **RAG**: n_ctx=2048, temperature=0.2, n_gpu_layers=0 (CPU)

---
test