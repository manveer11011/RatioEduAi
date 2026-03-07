#!/usr/bin/env python3
"""
Web UI for the RAG Study Assistant.
  python run_teacher_web.py
  open http://localhost:8765

Backend: RAG (documents + GGUF).
"""

import os
import sys
import time
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from rag_study_assistant.main import get_rag_backend

app = FastAPI(title="AI Teacher", version="1.0")
WEB_DIR = Path(__file__).resolve().parent / "web_ui"

MAX_MESSAGE_LENGTH = 32_000
RATE_LIMIT_REQUESTS = 60
RATE_LIMIT_WINDOW_SEC = 60
_rate_limit: dict[str, deque[float]] = {}

# Lazy backend init on first request
_backend = None  # (get_reply, get_reply_with_history, name)


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
        # Use directory of this file as project root so index is always loaded from the right place
        project_root = Path(__file__).resolve().parent
        _backend = get_rag_backend(project_root=project_root)
    return _backend


class ChatRequest(BaseModel):
    message: str
    history: list[dict] | None = None  # [{ "role": "user"|"assistant", "content": "..." }, ...]


class ChatResponse(BaseModel):
    reply: str


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
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error.")


@app.get("/api/status")
def api_status():
    try:
        _, _, name = _get_backend()
        return {"backend": name}
    except Exception as e:
        return {"backend": None, "error": str(e)}


if WEB_DIR.is_dir() and (WEB_DIR / "index.html").is_file():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
else:
    @app.get("/", response_class=HTMLResponse)
    def index():
        return HTMLResponse(
            "<h1>Web UI missing</h1><p>Expect web_ui/index.html in the project folder.</p>",
            status_code=404,
        )


def main():
    import uvicorn
    try:
        port = int(os.environ.get("PORT", "8765"))
    except (TypeError, ValueError):
        port = 8765
    host = os.environ.get("HOST", "127.0.0.1")
    print(f"AI Teacher web UI: http://{host}:{port}")
    print("Backend: RAG (documents + GGUF).")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
