#!/usr/bin/env python3
"""Web UI for RAG Study Assistant. Config: .env (PORT, HOST)."""

import os
import sys
import time
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import config
from app.chat_storage import delete_chat as storage_delete_chat
from app.chat_storage import get_chat as storage_get_chat
from app.chat_storage import load_chats as storage_load_chats
from app.chat_storage import save_chat as storage_save_chat
from rag_study_assistant.main import get_rag_backend

app = FastAPI(title="RatioEdu", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

MAX_MESSAGE_LENGTH = config.get_max_message_length()
RATE_LIMIT_REQUESTS = config.get_rate_limit_requests()
RATE_LIMIT_WINDOW_SEC = config.get_rate_limit_window_sec()
_rate_limit: dict[str, deque[float]] = {}

_backend = None


def _check_rate_limit(client_key: str) -> None:
    now = time.monotonic()
    if client_key not in _rate_limit:
        _rate_limit[client_key] = deque(maxlen=RATE_LIMIT_REQUESTS)
    q = _rate_limit[client_key]
    while q and q[0] < now - RATE_LIMIT_WINDOW_SEC:
        q.popleft()
    if len(q) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
    q.append(now)


def _get_backend():
    global _backend
    if _backend is None:
        project_root = Path(__file__).resolve().parent
        _backend = get_rag_backend(project_root=project_root)
    return _backend


class ChatRequest(BaseModel):
    message: str
    history: list[dict] | None = None


class ChatResponse(BaseModel):
    reply: str


class ChatBody(BaseModel):
    id: str | None = None
    title: str | None = None
    messages: list[dict] | None = None
    createdAt: int | float | None = None


@app.post("/api/chat", response_model=ChatResponse)
def api_chat(request: Request, body: ChatRequest):
    msg = (body.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Message is required")
    if len(msg) > MAX_MESSAGE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Message too long (max {MAX_MESSAGE_LENGTH} characters).",
        )
    client_key = request.client.host if request.client else "unknown"
    _check_rate_limit(client_key)
    try:
        get_reply, get_reply_with_history, _ = _get_backend()
        history = body.history or []
        if history:
            reply = get_reply_with_history(history, msg)
        else:
            reply = get_reply(msg)
        return ChatResponse(reply=reply)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
def api_status():
    try:
        _, _, name = _get_backend()
        return {"backend": name}
    except Exception as e:
        return {"backend": None, "error": str(e)}


# Chat history (persisted in chat_history/ for model context/memory)
@app.get("/api/chats")
def api_list_chats():
    """List all chats from chat_history folder."""
    return {"chats": storage_load_chats()}


@app.get("/api/chats/{chat_id}")
def api_get_chat(chat_id: str):
    """Get a single chat by id."""
    chat = storage_get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@app.post("/api/chats")
def api_create_chat(body: ChatBody):
    """Create or update a chat."""
    import random
    chat = {
        "id": body.id or f"chat-{int(time.time() * 1000)}-{random.randint(10000, 99999)}",
        "title": body.title or "New chat",
        "messages": body.messages or [],
        "createdAt": body.createdAt if body.createdAt is not None else int(time.time() * 1000),
    }
    storage_save_chat(chat)
    return chat


@app.put("/api/chats/{chat_id}")
def api_update_chat(chat_id: str, body: ChatBody):
    """Update an existing chat."""
    chat = storage_get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if body.title is not None:
        chat["title"] = body.title
    if body.messages is not None:
        chat["messages"] = body.messages
    storage_save_chat(chat)
    return chat


@app.delete("/api/chats/{chat_id}")
def api_delete_chat(chat_id: str):
    """Delete a chat."""
    if not storage_delete_chat(chat_id):
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"ok": True}


# Document upload: .txt and .pdf, stored under data/syllabus or data/notes
ALLOWED_DOCUMENT_TYPES = frozenset({"syllabus", "notes"})
ALLOWED_EXTENSIONS = frozenset({".txt", ".pdf"})


@app.post("/api/upload-document")
async def api_upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
):
    """Upload a .txt or .pdf file and store under data/syllabus or data/notes."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .txt and .pdf files are allowed.")
    doc_type = document_type.strip().lower()
    if doc_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="document_type must be 'syllabus' or 'notes'.",
        )
    project_root = Path(__file__).resolve().parent
    data_dir = project_root / "data" / doc_type
    data_dir.mkdir(parents=True, exist_ok=True)
    # Sanitize filename: keep only safe chars
    safe_name = "".join(c for c in file.filename if c.isalnum() or c in "._- ").strip() or f"document{ext}"
    dest = data_dir / safe_name
    try:
        content = await file.read()
        dest.write_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Rebuild RAG index immediately so new document is chunked and searchable
    try:
        from rag_study_assistant.main import build
        build()
        global _backend
        _backend = None  # force reload so next chat uses new index
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File saved but index rebuild failed: {e}") from e

    return {"ok": True, "path": str(dest.relative_to(project_root)).replace("\\", "/")}


@app.post("/api/rebuild-index")
def api_rebuild_index():
    """Rebuild the RAG index so newly uploaded documents are included."""
    try:
        from rag_study_assistant.main import build
        build()
        global _backend
        _backend = None  # force reload so next chat uses new index
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(
        "<h1>RatioEdu</h1><p>Use the Electron desktop app. API: /api/chat, /api/chats, /api/status</p>",
    )


def main():
    import uvicorn
    port = config.get_port()
    host = config.get_host()
    print(f"RatioEdu: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
